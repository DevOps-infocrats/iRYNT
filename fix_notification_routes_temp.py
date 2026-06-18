from app import create_app
from app.extensions import db
from app.modules.notifications.models import Notification

app = create_app()
with app.app_context():
    notes = Notification.query.filter(Notification.module == 'approvals').filter(Notification.route.like('/approvals/%')).all()
    print(f'Found {len(notes)} approvals notifications to update')
    for n in notes:
        n.route = n.route.replace('/approvals/', '/pending-approvals/view/')
        print('Updated', n.id, n.route)
    db.session.commit()
    print('Done')
