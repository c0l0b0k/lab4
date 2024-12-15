import os

from Neo4jDatabase import Neo4jDatabase
from UserDataController import *
from dotenv import load_dotenv

def get_access_token():
    while True:
        access_token = input("Введите токен доступа: ")
        if access_token.strip():  # Проверяем, что строка не пустая
            return access_token
        print("Токен доступа не может быть пустым. Попробуйте снова.")

def get_user_id():
    while True:
        user_id = input("Введите ID пользователя: ")
        if user_id.strip():  # Проверяем, что строка не пустая
            return user_id
        print("ID пользователя не может быть пустым. Попробуйте снова.")

def get_recursion_depth():
    while True:
        try:
            depth = int(input("Введите глубину рекурсии (>= 0, например, 2): "))
            if depth < 0:
                print("Глубина рекурсии должна быть неотрицательной.")
                continue
            return depth
        except ValueError:
            print("Некорректный ввод, попробуйте снова.")

def get_top_users_count():
    while True:
        try:
            top_users_count = int(input("Сколько топ пользователей по фолловерам показать? (>= 0, например, 5): "))
            if top_users_count < 0:
                print("Количество пользователей должно быть неотрицательным.")
                continue
            return top_users_count
        except ValueError:
            print("Некорректный ввод, попробуйте снова.")

def get_top_groups_count():
    while True:
        try:
            top_groups_count = int(input("Сколько популярных групп показать? (>= 0, например, 5): "))
            if top_groups_count < 0:
                print("Количество групп должно быть неотрицательным.")
                continue
            return top_groups_count
        except ValueError:
            print("Некорректный ввод, попробуйте снова.")

def check_internet_connection(url="http://www.google.com"):
    try:
        # Попытка сделать GET-запрос
        response = requests.get(url, timeout=3)  # Таймаут в 5 секунд
        return response.status_code == 200  # Возвращаем True, если статус 200
    except requests.ConnectionError:
        return False  # Возвращаем False, если произошла ошибка соединени

def main():

    if not check_internet_connection():
        logger.error("Нет подключения к интернету. Проверьте ваше соединение.")
        exit(1)  #

    access_token = get_access_token()
    user_id = get_user_id()
    depth = get_recursion_depth()
    top_users_count = get_top_users_count()
    top_groups_count = get_top_groups_count()

    user_data_collector = UserDataCollector(access_token)

    load_dotenv()
    # Чтение параметров из переменных окружения
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE")
    print(uri)

    # Создание экземпляра базы данных Neo4j и указание базы данных lab4
    db = Neo4jDatabase(uri=uri, user=user, password=password, database=database)

    try:
        db.delete_all_data()  # Очистка базы данных

        all_users = user_data_collector.fetch_data_recursive(user_id, max_depth=depth)
        for user in all_users:
            db.save_user(user)
            if not user.isEndTreeNode:
                for follower in user.followers:
                    db.save_follow_relation(user.id, follower)
                for group in user.subscriptions_groups:
                    db.save_group(group)
                    db.save_subscription_relation(user.id, group["id"])

        total_users = db.get_total_users()
        logger.info(f"Всего пользователей: {total_users}")

        total_groups = db.get_total_groups()
        logger.info(f"Всего групп: {total_groups}")

        # Запросы для топов и взаимных фолловеров
        if top_users_count > 0:
            top_users = db.get_top_users_by_followers(top_users_count)[:top_users_count]
            logger.info(f"Топ {top_users_count} пользователей с наибольшим количеством фолловеров: {top_users}")

        if top_groups_count > 0:
            top_groups = db.get_top_groups_by_followers(top_groups_count)[:top_groups_count]  # Замените на соответствующий метод
            logger.info(f"Топ {top_groups_count} популярных групп: {top_groups}")

        mutual_followers = db.get_mutual_followers()  # Замените на соответствующий метод
        logger.info(f"Пользователи, которые фолловят друг друга : {mutual_followers}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
