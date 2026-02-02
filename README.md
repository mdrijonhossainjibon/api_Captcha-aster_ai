# Python JSON Server

A simple REST API server built with Flask that provides JSON data storage and CRUD operations.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### General
- `GET /` - Server information and available endpoints
- `GET /data` - Get all stored data

### Users
- `GET /users` - Get all users
- `POST /users` - Create a new user
  ```json
  {
    "name": "John Doe",
    "email": "john@example.com"
  }
  ```
- `GET /users/<id>` - Get user by ID
- `PUT /users/<id>` - Update user
  ```json
  {
    "name": "Updated Name",
    "email": "updated@example.com"
  }
  ```
- `DELETE /users/<id>` - Delete user

### Posts
- `GET /posts` - Get all posts
- `POST /posts` - Create a new post
  ```json
  {
    "title": "Post Title",
    "content": "Post content",
    "author_id": 1
  }
  ```
- `GET /posts/<id>` - Get post by ID
- `PUT /posts/<id>` - Update post
- `DELETE /posts/<id>` - Delete post

## Data Storage

Data is stored in a `data.json` file with the following structure:
```json
{
  "users": [...],
  "posts": [...]
}
```

## Example Usage

### Create a user
```bash
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com"}'
```

### Get all users
```bash
curl http://localhost:5000/users
```

### Create a post
```bash
curl -X POST http://localhost:5000/posts \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Post", "content": "Hello World!", "author_id": 1}'
```
