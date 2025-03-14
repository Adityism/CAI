from flask import Blueprint, jsonify

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/info', methods=['GET'])
def get_faculty_info():
    # Sample data for faculty information
    faculty_data = [
        {
            "name": "Dr. Rajesh Kumar",
            "department": "Computer Science",
            "designation": "Professor",
            "email": "rajesh.kumar@upes.ac.in",
            "specialization": "Artificial Intelligence"
        },
        {
            "name": "Dr. Anjali Singh",
            "department": "Mathematics",
            "designation": "Associate Professor",
            "email": "anjali.singh@upes.ac.in",
            "specialization": "Statistics"
        }
    ]
    return jsonify(faculty_data)
