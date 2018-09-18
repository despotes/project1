SELECT title, author, year, isbn, COUNT(score), AVG(score)
FROM books JOIN reviews ON book_id = books.id WHERE books.isbn = '1402319462'
GROUP BY books.title;

SELECT COUNT(score), AVG(score) FROM reviews JOIN books ON book_id=books.id
WHERE books.isbn = '1402319462';