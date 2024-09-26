# crud/cms.py

from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from models.cms import Content, ContentItemProperty
from schemas.cms import ContentUpdate, ContentWithProperties, ItemContentProperty, BaseContent
from sqlalchemy.sql import func
from typing import List
import logging
from fastapi import HTTPException
from inflection import camelize
from sqlalchemy import and_

def custom_camelize(string: str) -> str:
    words = string.split()  # Split the string into words by spaces
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])

def create_root_content(db: Session, user_id: UUID):
    max_position = db.query(func.max(Content.position)).filter(Content.user_id == user_id).scalar() or 0
    new_position = max_position + 1
    
    db_root_content = Content(
        id=uuid4(),
        user_id=user_id,
        position=new_position,
        is_root=True,
    )
    db.add(db_root_content)
    db.commit()
    db.refresh(db_root_content)
    return db_root_content

def get_root_content(db: Session, content_id: UUID):
    db_root_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_root_content:
        return None, 404
        
    return db_root_content, 200

def get_users_root_contents(db: Session, user_id: UUID):
    db_root_contents = db.query(Content)\
        .filter(Content.user_id == user_id, Content.is_root == True)\
        .order_by(Content.position.asc())\
        .all()

    if not db_root_contents:
        return [], 404

    return db_root_contents, 200

def update_root_content(db: Session, content_id: UUID, alias: str):
    db_root_content = db.query(Content).filter(Content.id == content_id).first()
    
    if not db_root_content:
        return None, 404
    
    db_root_content.alias = alias
    db.commit()
    db.refresh(db_root_content)
    
    return db_root_content, 200

def delete_root_content(db: Session, content_id: UUID):
    db_root_content, status = get_root_content(db, content_id)
    db_root_content_id = db_root_content.id
    if db_root_content:
        db.delete(db_root_content)
        db.commit()
        
        db.query(Content).filter(Content.user_id == db_root_content.user_id, Content.position > db_root_content.position)\
            .update({Content.position: Content.position - 1})
        db.commit()

        delete_unused_properties_and_contents(db, db_root_content_id)

        return 200, True
    return 404, False

def update_content(db: Session, content_id: UUID, content: ContentUpdate):
    db_content = db.query(Content).filter(Content.id == content_id).first()
    
    if not db_content:
        return None, 404

    for key, value in content.dict(exclude_unset=True).items():
        setattr(db_content, key, value)
    db.commit()
    db.refresh(db_content)
    return db_content

def get_content(db: Session, content_id: UUID):
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content:
        raise HTTPException(status_code=404, detail="Content not found")

    # Fetch properties for item_content
    if db_content.item_content:
        properties = db.query(ContentItemProperty)\
            .filter(ContentItemProperty.id.in_(db_content.item_content))\
            .all()
        
        item_content_properties = [
            ItemContentProperty(
                content_id=prop.content_id,
                id=prop.id,
                key=prop.key
            )
            for prop in properties
        ]
    else:
        item_content_properties = []

    # Fetch properties for list_item_content (2D array of UUIDs)
    list_item_content_properties = []
    
    if db_content.list_item_content:
        # Iterate over the 2D array of UUIDs
        for item_list in db_content.list_item_content:
            resolved_item_list = []
            
            # Fetch properties for each UUID in the current list
            properties = db.query(ContentItemProperty)\
                .filter(ContentItemProperty.id.in_(item_list))\
                .all()

            resolved_item_list = [
                {
                    "id": str(prop.id),
                    "content_id": str(prop.content_id),
                    "key": prop.key
                }
                for prop in properties
            ]
            
            # Append the resolved properties for this list to the final 2D array
            list_item_content_properties.append(resolved_item_list)

    content_response = ContentWithProperties(
        id=db_content.id,
        user_id=db_content.user_id,
        position=db_content.position,
        content_type=db_content.content_type,
        text=db_content.text,
        image=db_content.image,
        html=db_content.html,
        list_text_content=db_content.list_text_content,
        item_content=item_content_properties,  # Vracíme pole objektů ItemContentProperty
        list_item_content=list_item_content_properties  # Vracíme pole pole objektů s id, content_id a key
    )

    return content_response

def create_new_item_property(db: Session, content_id: UUID, root_id: UUID):
    parent_content = db.query(Content).filter(Content.id == content_id).first()

    if not parent_content:
        return None, 404

    new_content = Content(
        id=uuid4(),
        user_id=parent_content.user_id,
        parent_content_id=content_id,
        root_content_id=root_id,
        position=0,
        is_root=False
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    new_property = ContentItemProperty(
        id=uuid4(),
        parent_content_id=content_id,
        root_content_id=root_id,
        user_id=parent_content.user_id,
        content_id=new_content.id,
        key="Klíč"
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    if parent_content.item_content is None:
        parent_content.item_content = []
    
    parent_content.item_content = parent_content.item_content + [new_property.id]
    
    db.commit()
    db.refresh(parent_content)

    return new_property, 201

def update_property(db: Session, property_id: UUID, key: str):
    prop = db.query(ContentItemProperty).filter(ContentItemProperty.id == property_id).first()

    if not prop:
        return None, 404

    prop.key = key

    db.commit()
    db.refresh(prop)
    
    return prop, 200

def create_empty_list_item_property_at_index(db: Session, content_id: UUID):
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content:
        return 404

    # Initialize as an empty 2D array if None
    if db_content.list_item_content is None:
        db_content.list_item_content = [[]]  # Initialize with a single empty list
    else:
        # Use the approach to add a new empty list without mutating the original
        db_content.list_item_content = db_content.list_item_content + [[]]

    db.commit()
    db.refresh(db_content)

    return 200

def add_property_to_list_item_content_at_index(db: Session, content_id: UUID, index: int, root_id: UUID):
    # Načteme obsah z databáze
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content:
        return 404

    # Zkontrolujeme, jestli `list_item_content` je None, pokud ano, inicializujeme jako prázdné dvourozměrné pole
    if db_content.list_item_content is None:
        db_content.list_item_content = []

    # Zajistíme, že pole má dostatečnou délku, přidáme prázdné pole až do požadovaného indexu
    while len(db_content.list_item_content) <= index:
        db_content.list_item_content.append([])

    new_content = Content(
        id=uuid4(),  # Vytvoření nového contentu s UUID
        user_id=db_content.user_id,
        root_content_id=root_id,
        parent_content_id=content_id,
        position=0,  # Nastav hodnotu podle potřeby
        is_root=False
    )
    db.add(new_content)
    db.commit()
    db.refresh(new_content)

    new_property = ContentItemProperty(
        id=uuid4(),
        root_content_id=root_id,
        parent_content_id=content_id,
        user_id=db_content.user_id,
        key="",
        content_id=new_content.id  # Použijeme ID nového contentu místo uuid4()
    )
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    # Přidáme nové ID do pole na daném indexu
    updated_list = db_content.list_item_content.copy()  # Vytvoříme kopii pole
    updated_list[index] = updated_list[index] + [str(new_property.id)]  # Přidáme nové ID
    db_content.list_item_content = updated_list  # Nastavíme kopii jako novou hodnotu

    # Uložíme změny do databáze
    db.commit()
    db.refresh(db_content)

    return 200

def delete_item_from_list_item_content(db: Session, content_id: UUID, index: int):
    # Fetch the content by ID
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content:
        return 404, "Content not found"

    if not db_content.list_item_content or len(db_content.list_item_content) <= index:
        return 400, "Invalid index or list_item_content does not exist"

    # Get the properties that are about to be deleted
    properties_to_check = db_content.list_item_content[index]

    # Remove the item from list_item_content
    updated_list = db_content.list_item_content[:index] + db_content.list_item_content[index + 1:]
    db_content.list_item_content = updated_list

    # Commit the changes
    db.commit()
    db.refresh(db_content)

    # Explicitly check and delete properties and their content if unused
    for property_id in properties_to_check:
        prop = db.query(ContentItemProperty).filter(ContentItemProperty.id == property_id).first()
        if prop:
            # Check if this property is used anywhere else in list_item_content or item_content
            used_in_other_content = db.query(Content).filter(
                and_(
                    Content.id != content_id,
                    or_(
                        Content.list_item_content.contains([property_id]),
                        Content.item_content.contains([property_id])
                    )
                )
            ).count()

            # If the property is not used elsewhere, delete it and its related content
            if used_in_other_content == 0:
                related_content_id = prop.content_id
                db.delete(prop)
                db.commit()

                # If related content exists and is not used elsewhere, delete it
                if related_content_id:
                    related_content = db.query(Content).filter(Content.id == related_content_id).first()
                    if related_content:
                        content_used_elsewhere = db.query(ContentItemProperty).filter(ContentItemProperty.content_id == related_content_id).count()
                        if content_used_elsewhere == 0 and not related_content.is_root:
                            db.delete(related_content)
                            db.commit()

    return 200, f"Item removed from list_item_content successfully, removed properties and content"

def reorder_list_item_content_in_db(db: Session, content_id: UUID, new_order: List[int]):
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content or db_content.list_item_content is None:
        return 404
    
    if len(db_content.list_item_content) != len(new_order):
        return 400
    
    content_map = {index: db_content.list_item_content[index] for index in range(len(db_content.list_item_content))}
    
    new_ordered_content = [content_map[new_index] for new_index in new_order]
    
    # Uložíme nově seřazený obsah
    db_content.list_item_content = new_ordered_content
    db.commit()
    db.refresh(db_content)

    return 200

# TODO: Deleting property ids from item_content ain't working as it should, find out why the id is still in the array
# TODO: deleting all child properties ain't solved yet
def delete_property_from_content(db: Session, content_id: UUID, property_id: UUID):
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content:
        return 404, "Content not found"

    if db_content.item_content:
        db_content.item_content = db.query(func.array_remove(db_content.item_content, property_id)).scalar()

    if db_content.list_item_content:
        updated_list_item_content = []
        for item_list in db_content.list_item_content:
            updated_item_list = [item for item in item_list if str(item) != str(property_id)]
            updated_list_item_content.append(updated_item_list)
        db_content.list_item_content = updated_list_item_content

    db.commit()
    db.refresh(db_content)

    delete_unused_properties_and_contents(db, db_content.root_content_id)

    return 200, "Property ID removed from content arrays successfully"

def transform_content(db: Session, content_id: UUID):
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if db_content.content_type == "text":
        return db_content.text

    if db_content.content_type == "image":
        return db_content.image

    if db_content.content_type == "html":
        return db_content.html

    if db_content.content_type == "list_text_content":
        return db_content.list_text_content
    
    if db_content.content_type == "item_content":
        item_content_ids = db_content.item_content

        db_properties = db.query(ContentItemProperty).filter(ContentItemProperty.id.in_(item_content_ids)).all()

        transformed_item_content = {}

        for prop in db_properties:
            transformed_item_content[custom_camelize(prop.key)] = transform_content(db, prop.content_id)

        return transformed_item_content

    if db_content.content_type == "list_item_content":
        list_item_content_ids = db_content.list_item_content

        transformed_list_item_content = []
        for item_content_ids in list_item_content_ids:  # Iterate over the 2D array
            transformed_item_content = {}
            db_properties = db.query(ContentItemProperty).filter(ContentItemProperty.id.in_(item_content_ids)).all()

            for prop in db_properties:
                transformed_item_content[custom_camelize(prop.key)] = transform_content(db, prop.content_id)

            transformed_list_item_content.append(transformed_item_content)

        return transformed_list_item_content

def get_root_public_content(db: Session, content_id: UUID):
    db_content = db.query(Content).filter(Content.id == content_id, Content.is_root == True).first()

    if not db_content:
        return None, 404

    output = {}

    if not db_content.alias:
        output[db_content.id] = transform_content(db, db_content.id)
    else:
        output[custom_camelize(db_content.alias)] = transform_content(db, db_content.id)

    return output

def delete_property_from_content(db: Session, content_id: UUID, property_id: UUID):
    db_content = db.query(Content).filter(Content.id == content_id).first()

    if not db_content:
        return 404, "Content not found"

    # Remove property from `item_content`
    if db_content.item_content:
        db_content.item_content = [prop_id for prop_id in db_content.item_content if prop_id != property_id]

    # Remove property from `list_item_content`
    if db_content.list_item_content:
        updated_list_item_content = []
        for item_list in db_content.list_item_content:
            updated_item_list = [item for item in item_list if str(item) != str(property_id)]
            updated_list_item_content.append(updated_item_list)
        db_content.list_item_content = updated_list_item_content

    # Commit after removing the property references from content
    db.commit()

    # Delete the property from the `ContentItemProperty` table
    prop_to_delete = db.query(ContentItemProperty).filter(ContentItemProperty.id == property_id).first()
    if prop_to_delete:
        db.delete(prop_to_delete)
        db.commit()

    # Check if the related content still exists and remove if unused
    related_content_id = prop_to_delete.content_id if prop_to_delete else None
    if related_content_id:
        related_content = db.query(Content).filter(Content.id == related_content_id).first()
        if related_content:
            # If no other properties reference this content, delete the content
            other_properties = db.query(ContentItemProperty).filter(ContentItemProperty.content_id == related_content_id).count()
            if other_properties == 0 and not related_content.is_root:
                db.delete(related_content)
                db.commit()

    return 200, "Property and associated content deleted successfully"

def delete_unused_properties_and_contents(db: Session, root_content_id: UUID):
    # Fetch all properties and contents with the given root_content_id
    properties = db.query(ContentItemProperty).filter(ContentItemProperty.root_content_id == root_content_id).all()
    contents = db.query(Content).filter(Content.root_content_id == root_content_id).all()

    # Identify all used property IDs by scanning through item_content and list_item_content across all content
    used_property_ids = set()

    # Query all the content globally to check for any references to properties
    all_contents = db.query(Content).all()

    for content in all_contents:
        # Check item_content for used properties
        if content.item_content:
            used_property_ids.update(content.item_content)

        # Check list_item_content (list of lists) for used properties
        if content.list_item_content:
            for item_list in content.list_item_content:
                used_property_ids.update(item_list)

    # Log used property ids for debugging
    logging.info(f"Used property ids: {used_property_ids}")

    # Find unused properties (those not in used_property_ids)
    unused_properties = [prop for prop in properties if prop.id not in used_property_ids]

    # Log unused properties for debugging
    logging.info(f"Unused properties: {unused_properties}")

    # Delete unused properties
    for prop in unused_properties:
        logging.info(f"Deleting unused property: {prop.id}")
        db.delete(prop)

        # Check if the content associated with this property is also unused and can be deleted
        if prop.content_id:
            related_content = db.query(Content).filter(Content.id == prop.content_id).first()
            if related_content:
                # Check if any other properties reference this content
                other_properties_referencing_content = db.query(ContentItemProperty).filter(
                    ContentItemProperty.content_id == related_content.id
                ).count()

                if other_properties_referencing_content == 0 and not related_content.is_root:
                    logging.info(f"Deleting related content: {related_content.id}")
                    db.delete(related_content)

    # Identify used content IDs by checking if any property refers to its content_id
    used_content_ids = set([prop.content_id for prop in properties if prop.content_id is not None])

    # Log used content ids for debugging
    logging.info(f"Used content ids: {used_content_ids}")

    # Find unused contents (no property refers to their content_id and they are not the root)
    unused_contents = [content for content in contents if content.id not in used_content_ids and not content.is_root]

    # Log unused contents for debugging
    logging.info(f"Unused contents: {unused_contents}")

    # Delete unused contents
    for content in unused_contents:
        logging.info(f"Deleting unused content: {content.id}")
        db.delete(content)

    # Commit the changes to the database
    db.commit()

    return {"detail": "Unused properties and contents deleted successfully"}
