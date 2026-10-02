// ---------- Helpers ----------
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const CSRF_TOKEN = getCookie('csrftoken');

function flashRowStatus(row, ok) {
  row.style.transition = 'background-color .3s';
  row.style.backgroundColor = ok ? 'rgba(33,181,115,.15)' : 'rgba(226,73,90,.15)';
  setTimeout(() => { row.style.backgroundColor = ''; }, 700);
}

// ---------- Attendance daily entry (AJAX save, no page reload) ----------
document.addEventListener('DOMContentLoaded', () => {
  const attendanceForm = document.getElementById('attendance-sheet');
  if (attendanceForm) {
    attendanceForm.addEventListener('change', async (e) => {
      const target = e.target;
      if (!target.classList.contains('att-field')) return;
      const row = target.closest('tr');
      const employeeId = row.dataset.employeeId;
      const date = attendanceForm.dataset.date;
      const status = row.querySelector('.att-status').value;
      const minutes = row.querySelector('.att-minutes').value || 0;
      const note = row.querySelector('.att-note').value || '';

      try {
        const resp = await fetch(SAVE_ATTENDANCE_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
          body: JSON.stringify({ employee_id: employeeId, date, status, minutes_late: minutes, note }),
        });
        const data = await resp.json();
        flashRowStatus(row, !!data.ok);
        if (!data.ok) {
          alert(data.error || "Erreur lors de l'enregistrement.");
        }
      } catch (err) {
        flashRowStatus(row, false);
        console.error(err);
      }
    });
  }

  // ---------- Dashboard: weekly attendance bar chart ----------
  const weekCanvas = document.getElementById('weekChart');
  if (weekCanvas && window.Chart && window.WEEK_CHART_DATA) {
    const d = window.WEEK_CHART_DATA;
    new Chart(weekCanvas, {
      type: 'bar',
      data: {
        labels: d.labels,
        datasets: [
          { label: 'Présents', data: d.present, backgroundColor: '#2f5fe0', borderRadius: 6, maxBarThickness: 22 },
          { label: 'Absents', data: d.absent, backgroundColor: '#e2495a', borderRadius: 6, maxBarThickness: 22 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: '#eef1fa' } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  // ---------- Dashboard: today's attendance donut ----------
  const donutCanvas = document.getElementById('todayDonut');
  if (donutCanvas && window.Chart && window.TODAY_COUNTS) {
    const c = window.TODAY_COUNTS;
    new Chart(donutCanvas, {
      type: 'doughnut',
      data: {
        labels: ['Présents', 'Absents', 'Retards', 'Non pointés'],
        datasets: [{
          data: [c.present, c.absent, c.late, c.not_recorded],
          backgroundColor: ['#2f5fe0', '#e2495a', '#e2a333', '#e6e9f5'],
          borderWidth: 0,
        }],
      },
      options: {
        cutout: '72%',
        plugins: { legend: { display: false } },
      },
    });
  }
});
