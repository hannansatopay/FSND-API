# API Reference

## Getting Started

- Base URL: At present this app can only be run locally and is not hosted as a base URL. The backend app is hosted at the default, `http://localhost:5000/`, which is set as a proxy in the frontend configuration.
- Authentication: This version of the application does not require authentication or API keys.



## Error Handling

Errors are returned as JSON objects in the following format:

```python
{
  "success": False,
  "error": 400,
  "message": "bad request",
}
```

The API will return four error types when requests fail:

- 400: Bad Request
- 404: Resource Not Found
- 422: Not Processable
- 500: Server Error (rare)

## Endpoints

The API call results are in the following JSON format:
  ```json
  {
    "success": true/false,
    // ... With other endpoint-specific fields ...
  }
  ```

> **Note:** The page size for any endpoint that supports pagination is **10**.

### GET /categories

Get all categories.

- Returns:
  - `success`: `True`
  - `categories`: ID to category mapping.


#### Sample

```bash
curl http://localhost:5000/categories
```

Result:

```json
{
  "success": true,
  "categories": {
    "1": "Science",
    "2": "Art",
    "3": "Geography",
    "4": "History",
    "5": "Entertainment",
    "6": "Sports"
  }
}
```

### GET /categories/{category_id}/questions

Retrieves questions in a specified category (optionally paginated).

- Returns:
  - `success`: `True`
  - `total_questions`: Number of questions in the specified category.
  - `questions`: Questions in the specified category.
- Resource parameters:
  - `category_id`: Category ID of questions to be fetched. The `0` ID will fetch all questions, regardless of categories.
- Query parameters:
  - `page`: (Optional) Page number for paginated results. If not given, or not positive, results are not paginated.
- Errors:
  - 404: Invalid `category_id`.
  
#### Sample

```bash
curl http://localhost:5000/categories/1/questions
```

Result:

```json
{
  "success": true,
  "total_questions": 3,
  "questions": [
    {
      "id": 20,
      "question": "What is the heaviest organ in the human body?",
      "answer": "The Liver",
      "category": 1,
      "difficulty": 4
    },
    ... // 2 more questions
  ]
}
```

#### Sample
```bash
curl http://localhost:5000/categories/0/questions?page=1
```

Result:

```json
{
  "success": true,
  "total_questions": 19,
  "questions": [
    {
      "id": 2,
      "question": "What movie earned Tom Hanks his third straight Oscar nomination, in 1996?",
      "answer": "Apollo 13",
      "category": 5,
      "difficulty": 4
    },
    ...  // 9 more questions
  ]
}
```

### GET /questions

Search questions.

- Returns:
  - `success`: `True`
  - `total_questions`: total number of questions returned
  - `questions`: search results
- Query parameters:
  - `search`: (Optional) Search term in question strings. If not given, all questions are returned (same as `/categories/0/questions`)
  - `page`: (Optional) Page number. If not given, or not positive, results are not paginated.

#### Sample

```bash
curl http://localhost:5000/questions?search=heaviest
```

Result:

```json
{
  "success": true,
  "total_questions": 1,
  "questions": [
    {
      "id": 20,
      "question":"What is the heaviest organ in the human body?",
      "answer": "The Liver",
      "category": 1,
      "difficulty": 4
    }
  ]
}
```

### POST /questions

Create a new question.

- Returns:
  - `success`: `True`
  - `id`: ID of the newly created question.
- Request Body (JSON):
  - `question`: Question string.
  - `answer`: Answer string.
  - `category`: ID of category this question belongs to (integer)
  - `difficulty`: Difficulty level (positive integer)
- Errors:
  - 400:
    - `category` is not an integer.
    - `difficulty` is not an integer.
  - 422:
    - Specified `category` not found.
    - `difficulty` is not positive.

#### Sample

```bash
curl -H "Content-Type: application/json" \
     -X POST \
     -d '{"question": "Test Question", "answer": "Test Ans", "category": 1, "difficulty": 1}' \
     http://localhost:5000/questions
```

Result:

```json
{
  "success": true,
  "id": 32
}
```

### GET /questions/{question_id}

Retrieve a question by ID.

- Returns:
  - `success`: `True`
  - `question`: Question with specified ID.
- Errors:
  - 404:
    - Question with specified ID not found.

#### Sample

```bash
curl http://localhost:5000/questions/20
```

Result:

```json
{
  "success": true,
  "question": {
    "id": 20,
    "question":"What is the heaviest organ in the human body?",
    "answer": "The Liver",
    "category": 1,
    "difficulty": 4
  }
}
```

### DELETE /questions/{question_id}

Delete a question by ID.

- Returns:
  - `success`: `True`
  - `id`: ID of the deleted question.
- Errors:
  - 404:
    - Question with specified ID not found.

#### Sample

```bash
curl -X DELETE http://localhost:5000/questions/1
```

Result:

```json
{
  "success": true,
  "id": 1
}
```

### POST /quizzes

Get a random question from the specified category different from the previous ones.

- Returns:
  - `success`: `True`
  - `question`: Question that is not any of the previous ones in the specified category. `null` is returned if such questions are exhausted.
- Request Body (JSON):
  - `previous_questions`: List of question IDs not to be excluded.
  - `quiz_category`: Category ID of the required question.
- Errors:
  - 400:
    - `previous_questions` is not a list
    - `quiz_category` is not an integer
  - 422:
    - `previous_questions` contains non-integral elements

#### Sample

```bash
curl -H "Content-Type: application/json" \
     -X POST \
     -D '{"previous_questions": [22], "quiz_category": 1}' \
     http://localhost:5000/quizzes
```

Result:

```json
{
  "success": true,
  "question": {
    "id": 20,
    "question":"What is the heaviest organ in the human body?",
    "answer": "The Liver",
    "category": 1,
    "difficulty": 4
  }
}
```
