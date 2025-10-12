import os
import shutil
from backend.app import create_app, setup_database

# Define the instance path
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')

# --- Force database recreation ---
if os.path.exists(instance_path):
    print("Existing 'instance' folder found. Deleting for a clean start.")
    shutil.rmtree(instance_path)

print("Creating new 'instance' folder.")
os.makedirs(instance_path)
# --- End of force recreation ---


app = create_app()

if __name__ == '__main__':
    # Set up the database first
    with app.app_context():
        print("Setting up the database...")
        setup_database(app)
        print("Database setup complete.")

    # Run the Flask app
    print("Starting Flask server on port 5001...")
    app.run(debug=True, port=5001)