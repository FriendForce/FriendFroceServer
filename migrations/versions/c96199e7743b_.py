"""empty message

Revision ID: c96199e7743b
Revises: d0cf3e8adf08
Create Date: 2019-08-04 13:16:38.094958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c96199e7743b'
down_revision = 'd0cf3e8adf08'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('website',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('raw_html', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('website')
    # ### end Alembic commands ###