from wtforms import Form, StringField, TextAreaField, PasswordField, SelectField, validators

class Edit_Profile(Form):
    username=StringField('User Name',[validators.Length(min=4, max=25)])
    email = StringField('Email',[validators.Length(min=6, max=50)])
    password = PasswordField('Password', [validators.DataRequired()])


