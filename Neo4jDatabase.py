from neo4j import GraphDatabase

class Neo4jDatabase:
    def __init__(self, uri, user, password, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database  # Сохраняем имя базы данных

    def close(self):
        self.driver.close()

    def save_user(self, user):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            session.execute_write(self._create_user_node, user)

    def save_follow_relation(self, user_id, follower_id):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            session.execute_write(self._create_follow_relation, user_id, follower_id)

    def save_subscription_relation(self, user_id, group_id):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            session.execute_write(self._create_subscription_relation, user_id, group_id)

    def query_top_5_users_by_followers(self):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            result = session.run(""" 
            MATCH (u:User)<-[:Follow]-(f:User) 
            RETURN u.id AS id, u.name AS name, COUNT(f) AS followers_count 
            ORDER BY followers_count DESC 
            LIMIT 5 
            """)
            return [{"id": record["id"], "name": record["name"], "followers_count": record["followers_count"]} for record in result]

    @staticmethod
    def _create_user_node(tx, user):
        query = """
        MERGE (u:User {id: $id})
        ON CREATE SET u.name = $name, u.sex = $sex, u.city = $city, u.screen_name = $screen_name
        ON MATCH SET u.name = $name, u.sex = $sex, u.city = $city, u.screen_name = $screen_name
        """
        tx.run(query, id=user.id, name=user.name, sex=user.sex, city=user.city, screen_name=user.screen_name)

    @staticmethod
    def _create_follow_relation(tx, user_id, follower_id):
        query = """
        MERGE (f:User {id: $follower_id})
        MERGE (u:User {id: $user_id})
        MERGE (f)-[:Follow]->(u)
        """
        tx.run(query, user_id=user_id, follower_id=follower_id)

    @staticmethod
    def _create_subscription_relation(tx, user_id, group_id):
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (g:Group {id: $group_id})
        MERGE (u)-[:Subscribe]->(g)
        """
        tx.run(query, user_id=user_id, group_id=group_id)

    def save_group(self, group):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            session.execute_write(self._create_group_node, group)

    def get_total_users(self):
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (u:User) RETURN COUNT(u) AS total_users")
            return result.single()["total_users"]

    def get_total_groups(self):
        with self.driver.session(database=self.database) as session:
            result = session.run("MATCH (g:Group) RETURN COUNT(g) AS total_groups")
            return result.single()["total_groups"]

    @staticmethod
    def _create_group_node(tx, group):
        query = """
        MERGE (g:Group {id: $id})
        ON CREATE SET g.name = $name, g.screen_name = $screen_name
        ON MATCH SET g.name = $name, g.screen_name = $screen_name
        """
        tx.run(query, id=group['id'], name=group['name'], screen_name=group.get('screen_name', ''))

    def delete_all_data(self):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            session.execute_write(self._delete_all_nodes)

    @staticmethod
    def _delete_all_nodes(tx):
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        tx.run(query)

    def get_mutual_followers(self):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            result = session.run(""" 
            MATCH (u1:User)-[:Follow]->(u2:User), (u2)-[:Follow]->(u1) 
            RETURN u1.id AS user1_id, u2.id AS user2_id 
            """)
            return [{"user1_id": record["user1_id"], "user2_id": record["user2_id"]} for record in result]

    def get_top_users_by_followers(self, count):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            result = session.run(""" 
            MATCH (u:User)<-[:Follow]-(f:User) 
            RETURN u.id AS id, u.name AS name, COUNT(f) AS followers_count 
            ORDER BY followers_count DESC 
            LIMIT $count 
            """, count=count)  # Здесь передаем параметр count

            return [{"id": record["id"], "name": record["name"], "followers_count": record["followers_count"]} for record in result]

    def get_top_groups_by_followers(self, count):
        with self.driver.session(database=self.database) as session:  # Указываем базу данных
            result = session.run(""" 
            MATCH (g:Group)<-[:Subscribe]-(u:User) 
            RETURN g.id AS id, g.name AS name, COUNT(u) AS followers_count 
            ORDER BY followers_count DESC 
            LIMIT $count 
            """, count=count)
            return [{"id": record["id"], "name": record["name"], "followers_count": record["followers_count"]} for record in result]
