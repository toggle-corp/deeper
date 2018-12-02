from deep.tests import TestCase

from user.models import User
from notification.models import Notification
from project.models import ProjectJoinRequest, Project

import logging
logger = logging.getLogger(__name__)


class TestNotification(TestCase):
    """Unit test for Notification"""
    def setUp(self):
        super().setUp()
        # Clear all notifications
        Notification.objects.all().delete()

    def test_notification_created_on_project_join_request(self):
        project = self.create(Project, role=self.admin_role)
        # Create users
        normal_user = self.create(User)
        admin_user = self.create(User)

        # Add admin user to project
        project.add_member(admin_user, role=self.admin_role)
        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )
        # Get notifications for admin_users
        for user in [self.user, admin_user]:
            notifications = Notification.get_for(user)
            assert notifications.count() == 1,\
                "A notification should have been created for admin"

            notification = notifications[0]
            assert notification.status == Notification.STATUS_UNSEEN
            assert notification.notification_type ==\
                Notification.PROJECT_JOIN_REQUEST
            assert notification.receiver == user
            # TODO: maybe, change join_request_id to id
            assert 'join_request_id' in notification.data,\
                "Notification data should have join_request_id"
            assert notification.data['join_request_id'] == join_request.pk

    def test_notification_updated_on_request_accepted(self):
        project = self.create(Project, role=self.admin_role)
        # Create users
        normal_user = self.create(User)

        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )

        # Get notification for self.user
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 1
        assert notifications[0].notification_type ==\
            Notification.PROJECT_JOIN_REQUEST

        # Update join_request by adding member
        project.add_member(join_request.requested_by, role=join_request.role)

        # Manually updateing join_request because add_member does not trigger
        # receiver for join_request post_save
        join_request.status = 'accepted'
        join_request.role = join_request.role
        join_request.save()

        # Get notifications
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 2
        assert notifications.filter(
            notification_type=Notification.PROJECT_JOIN_RESPONSE
        ).count() == 1

    def test_notification_updated_on_request_rejected(self):
        project = self.create(Project, role=self.admin_role)
        # Create users
        normal_user = self.create(User)

        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=normal_user,
            role=self.normal_role
        )

        # Get notification for self.user
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 1
        assert notifications[0].notification_type ==\
            Notification.PROJECT_JOIN_REQUEST

        # Update join_request without adding member
        join_request.status = 'rejected'
        join_request.role = join_request.role
        join_request.save()

        # Get notifications
        notifications = Notification.get_for(self.user)
        assert notifications.count() == 2
        assert notifications.filter(
            notification_type=Notification.PROJECT_JOIN_RESPONSE
        ).count() == 1


class TestNotificationAPIs(TestCase):
    def setUp(self):
        super().setUp()
        # Clean up notifications
        Notification.objects.all().delete()

    def test_get_notifications(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        url = '/api/v1/notifications/'
        data = {'project': project.id}

        self.authenticate()

        response = self.client.get(url, data)
        self.assert_200(response)

        data = response.data
        assert data['count'] == 0, "No notifications so far"

        # Now, create notifications
        self.create_join_request(project, user)

        response = self.client.get(url, data)
        self.assert_200(response)
        data = response.data
        assert data['count'] == 1, "A notification created for join request"
        result = data['results'][0]
        assert 'receiver' in result
        assert 'data' in result
        assert 'project' in result
        assert 'notificationType' in result
        assert 'receiver' in result
        assert 'status' in result
        assert result['status'] == 'unseen'
        # TODO: Check inside data

    def test_update_notification(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        url = '/api/v1/notifications/status/'

        # Create notification
        self.create_join_request(project, user)
        notifs = Notification.get_for(self.user)
        assert notifs.count() == 1
        assert notifs[0].status == Notification.STATUS_UNSEEN

        self.authenticate()

        data = [
            {'id': notifs[0].id, 'status': Notification.STATUS_SEEN}
        ]
        response = self.client.put(url, data)
        self.assert_200(response)

        # Check status
        notif = Notification.objects.get(id=notifs[0].id)
        assert notif.status == Notification.STATUS_SEEN

    def test_update_notification_invalid_data(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        url = '/api/v1/notifications/status/'

        # Create notification
        self.create_join_request(project, user)
        notifs = Notification.get_for(self.user)
        assert notifs.count() == 1
        assert notifs[0].status == Notification.STATUS_UNSEEN

        self.authenticate()

        # Let's send one valid and other invalid data, this should give 400
        data = [
            {
                'id': notifs[0].id + 1,
                'status': Notification.STATUS_SEEN + 'a'
            },
            {
                'id': notifs[0].id,
                'status': Notification.STATUS_SEEN
            },
        ]
        response = self.client.put(url, data)
        self.assert_400(response), "Invalid id and status should give 400"
        data = response.data
        assert 'errors' in data

    def create_join_request(self, project, user=None):
        """Create join_request"""
        user = user or self.create(User)
        join_request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=user,
            role=self.normal_role
        )
        return join_request
