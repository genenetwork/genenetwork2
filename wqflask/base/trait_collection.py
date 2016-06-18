class TraitCollection(object):
    
    def __init__(self, is_anon=False):
        self.is_anon = is_anon
        
        
    @app.route("/collections/remove", methods=('POST',))
    def remove_traits():
        if is_anon:
            AnonCollection.remove_traits()
        else:
            UserCollection.remove_traits()
            
        params = request.form
        print("params are:", params)
        uc_id = params['uc_id']
        uc = model.UserCollection.query.get(uc_id)
        traits_to_remove = params.getlist('traits[]')
        print("traits_to_remove are:", traits_to_remove)
        traits_to_remove = process_traits(traits_to_remove)
        print("\n\n  after processing, traits_to_remove:", traits_to_remove)
        all_traits = uc.members_as_set()
        print("  all_traits:", all_traits)
        members_now = all_traits - traits_to_remove
        print("  members_now:", members_now)
        print("Went from {} to {} members in set.".format(len(all_traits), len(members_now)))
        uc.members = json.dumps(list(members_now))
        uc.changed_timestamp = datetime.datetime.utcnow()
        db_session.commit()
    
        # We need to return something so we'll return this...maybe in the future
        # we can use it to check the results
        return str(len(members_now))

    def __init__(self, anon_id)
        self.anon_key = anon_key
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
