class DatabaseRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only allow migrations on the default database.
        """
        if db == 'default':
            return True

        return False
