from wqflask import user_manager
from wqflask.collect import (add_traits, remove_traits, process_traits,
                             num_members, get_members)
from parametrized_test import ParametrizedTest

class TestCollectionFunctions(ParametrizedTest):

    def testAddTraits(self):
        traits = ["trait1", "trait2"]
        expected_members = ["trait1", "trait2"]
        actual_coll = add_traits({"members":[]}, traits)
        self.assertEqual(actual_coll["members"], expected_members)

    def testRemoveTraits(self):
        expected_members = ["trait1", "trait3"]
        collection = remove_traits(
            {"members": ["trait1", "trait2", "trait3", "trait4"]},
            ["trait2", "trait4"])
        self.assertEqual(collection["members"], expected_members)

    def testProcessTraits(self):
        user_manager.actual_hmac_creation = lambda data: "dummy"
        traits_str = "trait1:dummy,trait2:dummy"
        actual_list = process_traits(traits_str)
        self.assertEqual(actual_list, set(["trait1", "trait2"]))

    def testNumMembers(self):
        expected = 2
        actual = num_members({"members":["trait1","trait2"]})
        self.assertEqual(actual, expected)

    def testGetMembers(self):
        self.assertEqual(
            get_members({"members":["trait1","trait2"]}),
            ["trait1", "trait2"])
