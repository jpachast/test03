const count = document.getElementById('count');
const increment = document.getElementById('increment');
const decrement = document.getElementById('decrement');

let currentCount = 0;

increment.addEventListener('click', () => {
    currentCount++;
    count.textContent = currentCount;
});

decrement.addEventListener('click', () => {
    currentCount--;
    count.textContent = currentCount;
});