async function loadGestures() {
  const res = await fetch('http://localhost:3000/api/gesture');
  const data = await res.json();
  const list = document.getElementById('gestureList');
  list.innerHTML = '';
  data.forEach(g => {
    const li = document.createElement('li');
    li.textContent = `${g.word} — ${new Date(g.timestamp).toLocaleString()}`;
    list.appendChild(li);
  });
}

setInterval(loadGestures, 2000); // refresh every 2 sec
loadGestures();
