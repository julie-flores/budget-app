async function loadDashboard() {
  const res = await fetch("http://127.0.0.1:5000/dashboard");
  const data = await res.json();

  document.getElementById("income").innerText = data.income;
  document.getElementById("expenses").innerText = data.expenses;
  document.getElementById("balance").innerText = data.balance;
}

loadDashboard();