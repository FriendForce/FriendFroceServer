"""empty message

Revision ID: 556f296952bc
Revises: 
Create Date: 2019-07-14 16:20:50.586579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '556f296952bc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('account',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('firebase_user_id', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('photo_url', sa.String(), nullable=True),
    sa.Column('person', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('connected_facebook', sa.Boolean(), nullable=True),
    sa.Column('connected_gmail', sa.Boolean(), nullable=True),
    sa.Column('connected_linkedin', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('firebase_user_id')
    )
    op.create_table('label',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.String(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('publicity', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('person',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('slug', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('is_user', sa.Boolean(), nullable=True),
    sa.Column('photo_url', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('tag',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('slug', sa.Text(), nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('originator', sa.Integer(), nullable=True),
    sa.Column('subject', sa.Integer(), nullable=True),
    sa.Column('originator_slug', sa.String(), nullable=True),
    sa.Column('subject_slug', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('publicity', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('label', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tag')
    op.drop_table('person')
    op.drop_table('label')
    op.drop_table('account')
    # ### end Alembic commands ###