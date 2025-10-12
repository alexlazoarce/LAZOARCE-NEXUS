from backend.app import create_app, setup_database

app = create_app()

if __name__ == '__main__':
    # The database setup is now handled by Flask-Migrate commands.
    # The `setup_database` function can be used for seeding if needed,
    # but we won't call it automatically on run.
    print("Starting Flask server on port 5001...")
    print("To manage database schema, use 'flask db' commands.")
    app.run(debug=True, port=5001)