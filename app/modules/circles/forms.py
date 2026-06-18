from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Regexp, ValidationError

from app.modules.circles.repository import CircleRepository
from app.modules.circles.validators import validate_circle_code, validate_circle_name


class CircleForm(FlaskForm):
    company_id = HiddenField()
    circle_id = HiddenField()
    circle_code = StringField(
        'Circle Code',
        filters=[lambda x: x.strip().upper() if x else x],
        validators=[
            DataRequired(message='Enter the circle code.'),
            Length(min=2, max=20, message='Circle code must be 2 to 20 characters.'),
            Regexp(r'^[A-Z0-9_-]+$', message='Circle code may only include uppercase letters, numbers, underscore and hyphen.'),
        ],
    )
    circle_name = StringField(
        'Circle Name',
        filters=[lambda x: x.strip() if x else x],
        validators=[DataRequired(message='Enter the circle name.'), Length(min=3, max=150, message='Circle name must be 3 to 150 characters.')],
    )
    regional_manager = StringField('Regional Manager', validators=[Optional(), Length(max=150)])
    email = StringField('Operational Email', validators=[Optional(), Length(max=120)])
    phone = StringField('Operational Phone', validators=[Optional(), Length(max=15)])
    address = TextAreaField('Circle Address', validators=[Optional(), Length(max=1000)])
    status = SelectField('Status', choices=[('Active', 'Active'), ('Inactive', 'Inactive')], default='Active')
    submit = SubmitField('Save Circle')

    def __init__(self, *args, company_id=None, circle_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_company_id = company_id
        self.form_circle_id = circle_id
        # Only set field data when an explicit value is provided; allow POSTed form data to populate otherwise
        if company_id is not None:
            self.company_id.data = company_id
        if circle_id is not None:
            self.circle_id.data = circle_id
        self.repository = CircleRepository()

    def validate_circle_code(self, field):
        if not validate_circle_code(field.data):
            raise ValidationError('Circle code must be 2-20 uppercase letters, numbers, underscore or hyphen.')
        if self.repository.exists_by_field('circle_code', field.data, company_id=self.form_company_id, exclude_id=self.form_circle_id):
            raise ValidationError('That circle code is already in use for the selected company.')

    def validate_circle_name(self, field):
        if not validate_circle_name(field.data):
            raise ValidationError('Circle name must be between 3 and 150 characters.')
