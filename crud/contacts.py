# # crud/contacts.py

# from sqlalchemy.orm import Session
# from models.contacts import Contact, Label, Form
# from schemas.contacts import ContactCreate, ContactUpdate, ContactLabelCreate, ContactLabelUpdate, FormCreate, FormUpdate
# from uuid import UUID, uuid4
# from utils.security import encrypt_data, decrypt_data, verify_token
# from models.user import User

# def get_user_by_email(db: Session, email: str):
#     return db.query(User).filter(User.email == email).first()

# def create_contact(db: Session, contact: ContactCreate, user: User, form_id: str):
#     encrypted_contact = {
#         "user_id": user.id,
#         "name": encrypt_data(contact.name, user.encryption_key) if contact.name else None,
#         "first_name": encrypt_data(contact.first_name, user.encryption_key) if contact.first_name else None,
#         "middle_name": encrypt_data(contact.middle_name, user.encryption_key) if contact.middle_name else None,
#         "last_name": encrypt_data(contact.last_name, user.encryption_key) if contact.last_name else None,
#         "company_name": encrypt_data(contact.company_name, user.encryption_key) if contact.company_name else None,
#         "job": encrypt_data(contact.job, user.encryption_key) if contact.job else None,
#         "country": encrypt_data(contact.country, user.encryption_key) if contact.country else None,
#         "state": encrypt_data(contact.state, user.encryption_key) if contact.state else None,
#         "city": encrypt_data(contact.city, user.encryption_key) if contact.city else None,
#         "postal_code": encrypt_data(contact.postal_code, user.encryption_key) if contact.postal_code else None,
#         "preffered_contact_method": encrypt_data(contact.preffered_contact_method, user.encryption_key) if contact.preffered_contact_method else None,
#         "preffered_contact_time": encrypt_data(contact.preffered_contact_time, user.encryption_key) if contact.preffered_contact_time else None,
#         "secondary_email": encrypt_data(contact.secondary_email, user.encryption_key) if contact.secondary_email else None,
#         "secondary_phone": encrypt_data(contact.secondary_phone, user.encryption_key) if contact.secondary_phone else None,
#         "referral_source": encrypt_data(contact.referral_source, user.encryption_key) if contact.referral_source else None,
#         "notes": encrypt_data(contact.notes, user.encryption_key) if contact.notes else None,
#         "email": encrypt_data(contact.email, user.encryption_key) if contact.email else None,
#         "phone": encrypt_data(contact.phone, user.encryption_key) if contact.phone else None,
#         "address": encrypt_data(contact.address, user.encryption_key) if contact.address else None,
#         "initial_message": encrypt_data(contact.initial_message, user.encryption_key) if contact.initial_message else None,
#         "agreed_to_privacy_policy": contact.agreed_to_privacy_policy,
#         "agreed_to_news_letter": contact.agreed_to_news_letter,
#         "seen": contact.seen,
#         "labels": contact.labels,
#         "description": encrypt_data(contact.description, user.encryption_key),
#         "form_id": form_id
#     }

#     db_contact = Contact(**encrypted_contact)
#     db.add(db_contact)
#     db.commit()
#     db.refresh(db_contact)

#     return db_contact

# def get_contact(db: Session, contact_id: UUID, user: User):
#     db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
#     if db_contact:
#         decrypted_contact = decrypt_contact(db_contact, user.encryption_key)
#         return decrypted_contact
#     return None

# def get_contacts(db: Session, user_id: UUID, user: User):
#     db_contacts = db.query(Contact).filter(Contact.user_id == user_id).all()
#     decrypted_contacts = [decrypt_contact(contact, user.encryption_key) for contact in db_contacts]
#     if not decrypted_contacts:
#         return []
#     return decrypted_contacts

# def update_contact(db: Session, contact_id: UUID, contact_update: dict, user: User):
#     db_contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).first()
#     if not db_contact:
#         return None
#     for key, value in contact_update.items():
#         if isinstance(value, list) or isinstance(value, bool):
#             setattr(db_contact, key, value)
#         else:
#             setattr(db_contact, key, encrypt_data(value, user.encryption_key) if value else value)
#     db.commit()
#     db.refresh(db_contact)
#     return decrypt_contact(db_contact, user.encryption_key)

# def delete_contact(db: Session, contact_id: UUID, user: User):
#     db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
#     if db_contact:
#         db.delete(db_contact)
#         db.commit()
#         return True
#     return False

# def verify_user_and_get_contact(db: Session, contact_id: UUID, token: str) -> (int, Contact):
#     contact = db.query(Contact).filter(Contact.id == contact_id).first()
#     if not contact:
#         return 404, None
#     user_id = contact.user_id
#     if not verify_token(db, user_id, token):
#         return 401, None
#     return 200, contact

# def decrypt_contact(contact: Contact, encryption_key):
#     def decrypt_or_none(data, key):
#         decrypted_data = decrypt_data(data, key)
#         if decrypted_data is not None:
#             return decrypted_data if decrypted_data else None

#     decrypted_contact = {
#         "id": contact.id,
#         "user_id": contact.user_id,
#         "name": decrypt_or_none(contact.name, encryption_key),
#         "first_name": decrypt_or_none(contact.first_name, encryption_key),
#         "middle_name": decrypt_or_none(contact.middle_name, encryption_key),
#         "last_name": decrypt_or_none(contact.last_name, encryption_key),
#         "company_name": decrypt_or_none(contact.company_name, encryption_key),
#         "job": decrypt_or_none(contact.job, encryption_key),
#         "country": decrypt_or_none(contact.country, encryption_key),
#         "state": decrypt_or_none(contact.state, encryption_key),
#         "city": decrypt_or_none(contact.city, encryption_key),
#         "postal_code": decrypt_or_none(contact.postal_code, encryption_key),
#         "preffered_contact_method": decrypt_or_none(contact.preffered_contact_method, encryption_key),
#         "preffered_contact_time": decrypt_or_none(contact.preffered_contact_time, encryption_key),
#         "secondary_email": decrypt_or_none(contact.secondary_email, encryption_key),
#         "secondary_phone": decrypt_or_none(contact.secondary_phone, encryption_key),
#         "referral_source": decrypt_or_none(contact.referral_source, encryption_key),
#         "notes": decrypt_or_none(contact.notes, encryption_key),
#         "email": decrypt_or_none(contact.email, encryption_key),
#         "phone": decrypt_or_none(contact.phone, encryption_key),
#         "address": decrypt_or_none(contact.address, encryption_key),
#         "initial_message": decrypt_or_none(contact.initial_message, encryption_key),
#         "agreed_to_privacy_policy": contact.agreed_to_privacy_policy,
#         "agreed_to_news_letter": contact.agreed_to_news_letter,
#         "created_at": contact.created_at,
#         "updated_at": contact.updated_at,
#         "seen": contact.seen,
#         "labels": contact.labels,
#         "description": decrypt_or_none(contact.description, encryption_key),
#         "form_id": contact.form_id
#     }
#     return decrypted_contact

# def get_label(db: Session, label_id: UUID):
#     db_label = db.query(Label).filter(Label.id == label_id).first()
#     if db_label:
#         return 200, db_label
#     return 404, None
    
# def get_labels(db: Session, user_id: UUID):
#     db_labels = db.query(Label).filter(Label.user_id == user_id).all()
#     if db_labels:
#         return 200, db_labels
#     return 404, None

# def create_label(db: Session, label: ContactLabelCreate, user_id: UUID):
#     db_label = Label(
#         id=uuid4(),
#         user_id=user_id,
#         color=label.color,
#         title=label.title,
#     )
#     db.add(db_label)
#     db.commit()
#     db.refresh(db_label)
#     return db_label

# def update_label(db: Session, label_id: UUID, label: ContactLabelUpdate):
#     status, db_label =  get_label(db, label_id)
#     if not db_label:
#         return 404, None
#     for key, value in label.dict(exclude_unset=True).items():
#         setattr(db_label, key, value)
#     db.commit()
#     db.refresh(db_label)
#     return db_label

# def delete_label(db: Session, label_id: UUID):
#     status, db_label = get_label(db, label_id)
#     if db_label:
#         db.delete(db_label)
#         db.commit()
#         return 200, True
#     return 404, False

# def get_form(db: Session, form_id: UUID):
#     db_form = db.query(Form).filter(Form.id == form_id).first()
#     if db_form:
#         return 200, db_form
#     return 404, None

# def get_forms(db: Session, user_id: UUID):
#     db_forms = db.query(Form).filter(Form.user_id == user_id).all()
#     if db_forms:
#         return 200, db_forms
#     return 404, None

# def create_form(db: Session, form: FormCreate, user_id: UUID):
#     db_form = Form(
#         id=uuid4(),
#         user_id=user_id,
#         name=form.name,
#         description=form.description,
#         form_properties=form.form_properties,
#     )
#     db.add(db_form)
#     db.commit()
#     db.refresh(db_form)
#     return db_form

# def update_form(db: Session, form_id: UUID, form: FormUpdate):
#     status, db_form = get_form(db, form_id)
#     if not db_form:
#         return 404, None
#     for key, value in form.dict(exclude_unset=True).items():
#         setattr(db_form, key, value)
#     db.commit()
#     db.refresh(db_form)
#     return db_form

# def delete_form(db: Session, form_id: UUID):
#     status, db_form = get_form(db, form_id)
#     if db_form:
#         db.delete(db_form)
#         db.commit()
#         return 200, True
#     return 404, False
