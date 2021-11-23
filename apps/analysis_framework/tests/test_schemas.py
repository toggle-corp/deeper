import factory

from utils.graphene.tests import GraphQLSnapShotTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from analysis_framework.factories import (
    AnalysisFrameworkFactory,
    SectionFactory,
    WidgetFactory,
)


class TestAnalysisFrameworkQuery(GraphQLSnapShotTestCase):
    factories_used = [AnalysisFrameworkFactory, SectionFactory, WidgetFactory, ProjectFactory]

    def test_analysis_framework_list(self):
        query = '''
            query MyQuery {
              analysisFrameworks (ordering: "id") {
                page
                pageSize
                totalCount
                results {
                  id
                  title
                  description
                  isPrivate
                }
              }
            }
        '''

        user = UserFactory.create()
        private_af = AnalysisFrameworkFactory.create(is_private=True)
        normal_af = AnalysisFrameworkFactory.create()
        member_af = AnalysisFrameworkFactory.create()
        member_af.add_member(user)

        # Without login
        self.query_check(query, assert_for_error=True)

        # With login
        self.force_login(user)

        content = self.query_check(query)
        results = content['data']['analysisFrameworks']['results']
        self.assertEqual(content['data']['analysisFrameworks']['totalCount'], 2)
        self.assertIdEqual(results[0]['id'], normal_af.id)
        self.assertIdEqual(results[1]['id'], member_af.id)
        self.assertNotIn(str(private_af.id), [d['id'] for d in results])  # Can't see private project.

        project = ProjectFactory.create(analysis_framework=private_af)
        # It shouldn't list private AF after adding to a project.
        content = self.query_check(query)
        results = content['data']['analysisFrameworks']['results']
        self.assertEqual(content['data']['analysisFrameworks']['totalCount'], 2)
        self.assertNotIn(str(private_af.id), [d['id'] for d in results])  # Can't see private project.

        project.add_member(user)
        # It should list private AF after user is member of the project.
        content = self.query_check(query)
        results = content['data']['analysisFrameworks']['results']
        self.assertEqual(content['data']['analysisFrameworks']['totalCount'], 3)
        self.assertIn(str(private_af.id), [d['id'] for d in results])  # Can see private project now.

    def test_analysis_framework(self):
        query = '''
            query MyQuery ($id: ID!) {
              analysisFramework(id: $id) {
                id
                currentUserRole
                description
                isPrivate
                title
              }
            }
        '''

        user = UserFactory.create()
        private_af = AnalysisFrameworkFactory.create(is_private=True)
        normal_af = AnalysisFrameworkFactory.create()
        member_af = AnalysisFrameworkFactory.create()
        member_af.add_member(user)
        # Without login
        self.query_check(query, assert_for_error=True, variables={'id': normal_af.pk})

        # With login
        self.force_login(user)

        # Should work for normal AF
        response = self.query_check(query, variables={'id': normal_af.pk})['data']['analysisFramework']
        self.assertIdEqual(response['id'], normal_af.id, response)
        self.assertEqual(response['isPrivate'], False, response)
        # Should work for member AF
        response = self.query_check(query, variables={'id': member_af.pk})['data']['analysisFramework']
        self.assertIdEqual(response['id'], member_af.id, response)
        self.assertEqual(response['isPrivate'], False, response)
        # Shouldn't work for non-member private AF
        response = self.query_check(query, variables={'id': private_af.pk})['data']['analysisFramework']
        self.assertEqual(response, None, response)
        # Shouldn't work for non-member private AF even if there is a project attached
        project = ProjectFactory.create(analysis_framework=private_af)
        response = self.query_check(query, variables={'id': private_af.pk})['data']['analysisFramework']
        self.assertEqual(response, None, response)
        # Should work for member private AF
        project.add_member(user)
        response = self.query_check(query, variables={'id': private_af.pk})['data']['analysisFramework']
        self.assertIdEqual(response['id'], private_af.id, response)
        self.assertEqual(response['isPrivate'], True, response)

    def test_analysis_framework_detail_query(self):
        query = '''
            query MyQuery ($id: ID!) {
              analysisFramework(id: $id) {
                id
                currentUserRole
                description
                isPrivate
                title
                secondaryTagging {
                  id
                  key
                  title
                  widgetId
                  order
                  properties
                }
                primaryTagging {
                  id
                  title
                  order
                  tooltip
                  widgets {
                    id
                    key
                    title
                    widgetId
                    order
                    properties
                  }
                }
               members {
                  id
                  joinedAt
                  addedBy {
                    id
                    displayName
                  }
                  member {
                    id
                    displayName
                  }
                  role {
                    id
                    title
                  }
                }
                visibleProjects {
                    id
                    title
                }
              }
            }
        '''

        user = UserFactory.create()
        another_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        af.add_member(another_user)
        project = ProjectFactory.create(analysis_framework=af, is_private=False)
        private_project = ProjectFactory.create(analysis_framework=af, is_private=True)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'id': af.pk}, **kwargs)

        # Without login
        _query_check(assert_for_error=True)

        # With login
        self.force_login(user)

        # Should work for normal AF
        response = _query_check()['data']['analysisFramework']
        self.assertEqual(len(response['secondaryTagging']), 0, response)
        self.assertEqual(len(response['primaryTagging']), 0, response)
        self.assertEqual(len(response['visibleProjects']), 1, response)
        self.assertListIds(
            response['visibleProjects'],
            [project],
            response
        )
        # lets add member to the private_project
        private_project.add_member(user)
        response = _query_check()['data']['analysisFramework']
        self.assertEqual(len(response['visibleProjects']), 2, response)
        self.assertListIds(
            response['visibleProjects'],
            [project, private_project],
            response
        )
        # Let's add some widgets and sections
        sequence = factory.Sequence(lambda n: n)
        rsequence = factory.Sequence(lambda n: 20 - n)
        # Primary Tagging
        for order, widget_count, tooltip, _sequence in (
            (3, 2, 'Some tooltip info 101', sequence),
            (1, 3, 'Some tooltip info 102', rsequence),
            (2, 4, 'Some tooltip info 103', sequence),
        ):
            section = SectionFactory.create(analysis_framework=af, order=order, tooltip=tooltip)
            WidgetFactory.create_batch(widget_count, analysis_framework=af, section=section, order=_sequence)
            WidgetFactory.reset_sequence()
        # Secondary Tagging
        WidgetFactory.create_batch(4, analysis_framework=af, order=rsequence)

        # Let's save/compare snapshot (without membership)
        response = _query_check()
        self.assertMatchSnapshot(response, 'without-membership')

        # Let's save/compare snapshot (with membership)
        af.add_member(user)
        response = _query_check()
        self.assertMatchSnapshot(response, 'with-membership')

    def test_recent_analysis_framework(self):
        # NOTE: This test includes the recent_analysis_framework based on project and source
        query = '''
                query MyQuery {
                  projectExploreStats {
                    topActiveFrameworks {
                      analysisFrameworkId
                      analysisFrameworkTitle
                      projectCount
                      sourceCount
                    }
                  }
                }
            '''

        user = UserFactory.create()

        # lets create some analysis_framework
        analysis_framework1 = AnalysisFrameworkFactory.create()
        analysis_framework2 = AnalysisFrameworkFactory.create()
        analysis_framework3 = AnalysisFrameworkFactory.create()
        analysis_framework4 = AnalysisFrameworkFactory.create()
        analysis_framework5 = AnalysisFrameworkFactory.create()
        analysis_framework6 = AnalysisFrameworkFactory.create()

        project1 = ProjectFactory.create(analysis_framework=analysis_framework1)
        project2 = ProjectFactory.create(analysis_framework=analysis_framework2)
        project3 = ProjectFactory.create(analysis_framework=analysis_framework1)
        project4 = ProjectFactory.create(analysis_framework=analysis_framework3)
        project5 = ProjectFactory.create(analysis_framework=analysis_framework4)
        project6 = ProjectFactory.create(analysis_framework=analysis_framework3)
        project7 = ProjectFactory.create(analysis_framework=analysis_framework1)
        project8 = ProjectFactory.create(analysis_framework=analysis_framework5)
        project9 = ProjectFactory.create(analysis_framework=analysis_framework6)

        # some lead for the project
        LeadFactory.create_batch(15, project=project1)
        LeadFactory.create_batch(13, project=project2)
        LeadFactory.create_batch(20, project=project3)
        LeadFactory.create_batch(20, project=project4)
        LeadFactory.create_batch(20, project=project5)
        LeadFactory.create_batch(30, project=project6)
        LeadFactory.create_batch(30, project=project7)
        LeadFactory.create_batch(30, project=project8)
        LeadFactory.create_batch(30, project=project9)

        # -- Without login
        self.query_check(query, assert_for_error=True)

        # -- With login
        self.force_login(user)

        content = self.query_check(query)
        print(content)

        self.assertEqual(len(content['data']['projectExploreStats']['topActiveFrameworks']), 5, content)
        self.assertEqual(
            content['data']['projectExploreStats']['topActiveFrameworks'][0]['analysisFrameworkId'],
            str(analysis_framework1.id)
        )
        self.assertEqual(content['data']['projectExploreStats']['topActiveFrameworks'][0]['projectCount'], 3)
        self.assertEqual(content['data']['projectExploreStats']['topActiveFrameworks'][0]['sourceCount'], 65)
        self.assertEqual(
            content['data']['projectExploreStats']['topActiveFrameworks'][1]['analysisFrameworkId'],
            str(analysis_framework3.id)
        )
        self.assertEqual(content['data']['projectExploreStats']['topActiveFrameworks'][1]['projectCount'], 2)
        self.assertEqual(
            content['data']['projectExploreStats']['topActiveFrameworks'][2]['analysisFrameworkId'],
            str(analysis_framework5.id)
        )
        self.assertEqual(
            content['data']['projectExploreStats']['topActiveFrameworks'][3]['analysisFrameworkId'],
            str(analysis_framework6.id)
        )
        self.assertEqual(
            content['data']['projectExploreStats']['topActiveFrameworks'][4]['analysisFrameworkId'],
            str(analysis_framework4.id)
        )
