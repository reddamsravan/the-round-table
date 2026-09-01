<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Day {N}: {Title} -- {topic}</title>
  <link rel="stylesheet" href="lesson.css">
</head>
<body>

  <h1>Day {N}: {Title}</h1>

  <blockquote class="meta">
    <strong>Curriculum</strong>: {topic} |
    <strong>Level</strong>: {level} |
    <strong>Time budget</strong>: {time_budget} min |
    <strong>Goal</strong>: {goal}
  </blockquote>

  <!-- 1. Learning Objectives -->
  <section class="objectives">
    <h2>Learning Objectives</h2>
    <ul>
      <li>{Objective}</li>
    </ul>
  </section>

  <!-- 2. Concept Explanation -->
  <section class="concept">
    <h2>Concept Explanation</h2>
    <p>{prose explanation placeholder}</p>
  </section>

  <!-- 3. Real-World Examples -->
  <section class="examples">
    <h2>Real-World Examples</h2>
    <article>
      <p><strong>Example 1:</strong> {description placeholder}</p>
    </article>
    <article>
      <p><strong>Example 2:</strong> {description placeholder}</p>
    </article>
  </section>

  <!-- 4. Comprehension Questions -->
  <section class="questions">
    <h2>Comprehension Questions</h2>
    <p>Answer each question in your own words before revealing the answer.</p>

    <p><strong>Question 1:</strong> {question}</p>
    <details>
      <summary>Show answer</summary>
      <p>{answer}</p>
    </details>

    <p><strong>Question 2:</strong> {question}</p>
    <details>
      <summary>Show answer</summary>
      <p>{answer}</p>
    </details>
  </section>

  <!-- 5. Practical Tasks -->
  <section class="tasks">
    <h2>Practical Tasks</h2>

    <h3>Core Task (15 to 30 min)</h3>
    <p>{description}</p>
    <p>Done when:</p>
    <ul>
      <li><label><input type="checkbox"> {criterion}</label></li>
    </ul>

    <h3>Stretch Task (45 to 90 min)</h3>
    <p>{description}</p>
    <p>Done when:</p>
    <ul>
      <li><label><input type="checkbox"> {criterion}</label></li>
    </ul>
  </section>

  <!-- 6. Further Reading -->
  <section class="reading">
    <h2>Further Reading</h2>
    <ul>
      <li>{book}</li>
      <li>{documentation}</li>
      <li>{search term}</li>
    </ul>
  </section>

</body>
</html>
