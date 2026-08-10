import streamlit as st
import bcrypt

from database import register_user, get_user


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode(),
        hashed_password.encode()
    )


def register(username, email, password):
    hashed = hash_password(password)
    return register_user(username, email, hashed)


def login(username, password):

    user = get_user(username)

    if user is None:
        return False

    if verify_password(password, user["password"]):
        st.session_state.logged_in = True
        st.session_state.user_id = user["id"]
        st.session_state.username = user["username"]
        return True

    return False


def logout():
    st.session_state.clear()