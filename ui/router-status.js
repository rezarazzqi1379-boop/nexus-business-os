fetch('/v1/console/router').then(response => response.json()).then(status => {
  document.getElementById('status').textContent = JSON.stringify(status, null, 2);
}).catch(() => {
  document.getElementById('status').textContent = 'Unavailable';
});
