class AnonCollection(TraitCollection):
    
    def __init__(self, anon_id)
        self.anon_id = anon_id
        self.collection_members = Redis.smembers(self.anon_id)
        print("self.collection_members is:", self.collection_members)
        self.num_members = len(self.collection_members)
        

    @app.route("/collections/remove", methods=('POST',))
    def remove_traits(traits_to_remove):
        print("traits_to_remove:", traits_to_remove)
        for trait in traits_to_remove:
            Redis.srem(self.anon_id, trait)
        members_now = self.collection_members - traits_to_remove
        print("members_now:", members_now)
        print("Went from {} to {} members in set.".format(len(self.collection_members), len(members_now)))

        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len(members_now))
