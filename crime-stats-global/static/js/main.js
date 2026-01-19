// ============================================
// GLOBAL VARIABLES
// ============================================
let homicideChart = null;

// ============================================
// THEME TOGGLE FUNCTIONALITY
// ============================================
function toggleTheme() {
  const body = document.body;
  const currentTheme = body.classList.contains('light-theme') ? 'light' : 'dark';
  
  if (currentTheme === 'dark') {
    body.classList.add('light-theme');
    localStorage.setItem('theme', 'light');
  } else {
    body.classList.remove('light-theme');
    localStorage.setItem('theme', 'dark');
  }
  
  // Update chart colors when theme changes
  if (homicideChart) {
    updateChartTheme();
  }
}

// Load saved theme on page load
function loadSavedTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
    document.body.classList.add('light-theme');
  }
}

// ============================================
// COUNTRY FORM SUBMISSION
// ============================================
function handleCountrySubmit(event) {
  event.preventDefault();
  const country = document.getElementById('country').value;
  if (country) {
    window.location.href = '/country/' + encodeURIComponent(country);
  }
}

// Auto-submit on selection change
document.addEventListener('DOMContentLoaded', function() {
  // Load saved theme
  loadSavedTheme();
  
  // Country selection auto-submit
  const countrySelect = document.getElementById('country');
  if (countrySelect) {
    countrySelect.addEventListener('change', function(e) {
      if (this.value) {
        handleCountrySubmit(e);
      }
    });
  }
  
  // Load live homicide data
  loadLiveHomicideData();
  
  // Load Telangana crime news
  loadTelanganaNews();
});

// ============================================
// LIVE HOMICIDE DATA - World Bank API
// ============================================
async function loadLiveHomicideData() {
  try {
    // Default to India (IN) - you can change this or make it dynamic
    const countryCode = 'IN';
    const url = `https://api.worldbank.org/v2/country/${countryCode}/indicator/VC.IHR.PSRC.P5?format=json&per_page=100`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    if (!data || data.length < 2) {
      console.error('No data available from World Bank API');
      return;
    }
    
    const records = data[1];
    const years = [];
    const values = [];
    
    // Filter data for years 2000-2024
    records.forEach(entry => {
      const year = parseInt(entry.date);
      const value = entry.value;
      
      if (year >= 2000 && year <= 2024 && value !== null) {
        years.push(year);
        values.push(parseFloat(value));
      }
    });
    
    // Reverse to get chronological order (oldest to newest)
    years.reverse();
    values.reverse();
    
    // Update latest stat
    if (values.length > 0) {
      const latestValue = values[values.length - 1];
      const latestYear = years[years.length - 1];
      document.getElementById('latest-rate').textContent = 
        `${latestValue.toFixed(1)} per 100k (${latestYear})`;
    }
    
    // Create chart
    createHomicideChart(years, values);
    
  } catch (error) {
    console.error('Error fetching homicide data:', error);
    document.getElementById('latest-rate').textContent = 'Data unavailable';
  }
}

// ============================================
// CHART CREATION
// ============================================
function createHomicideChart(years, values) {
  const ctx = document.getElementById('homicideChart');
  if (!ctx) return;
  
  const isDarkTheme = !document.body.classList.contains('light-theme');
  const gridColor = isDarkTheme ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
  const tickColor = isDarkTheme ? '#aaa' : '#666';
  
  homicideChart = new Chart(ctx.getContext('2d'), {
    type: 'line',
    data: {
      labels: years,
      datasets: [{
        label: 'Homicides per 100k',
        data: values,
        borderColor: '#ff6b6b',
        backgroundColor: 'rgba(255, 107, 107, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#ff6b6b',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 2.5,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 12,
          titleColor: '#fff',
          bodyColor: '#fff',
          callbacks: {
            label: function(context) {
              return context.parsed.y.toFixed(2) + ' per 100k';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          grid: {
            color: gridColor
          },
          ticks: {
            color: tickColor,
            callback: function(value) {
              return value.toFixed(1);
            }
          }
        },
        x: {
          grid: {
            color: 'rgba(255, 255, 255, 0.05)'
          },
          ticks: {
            color: tickColor
          }
        }
      }
    }
  });
}

// Update chart theme when toggled
function updateChartTheme() {
  if (!homicideChart) return;
  
  const isDarkTheme = !document.body.classList.contains('light-theme');
  const gridColor = isDarkTheme ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
  const tickColor = isDarkTheme ? '#aaa' : '#666';
  
  homicideChart.options.scales.y.grid.color = gridColor;
  homicideChart.options.scales.y.ticks.color = tickColor;
  homicideChart.options.scales.x.ticks.color = tickColor;
  
  homicideChart.update();
}


async function loadTelanganaNews() {
  const newsLoading = document.getElementById('news-loading');
  const newsList = document.getElementById('news-list');
  
  try {
    const response = await fetch('/api/telangana-crime-news');
    const data = await response.json();
    
    if (newsLoading) {
      newsLoading.style.display = 'none';
    }
    
    if (!newsList) return;
    
    if (data.articles && data.articles.length > 0) {
      newsList.innerHTML = '';
      
      data.articles.forEach(article => {
        const li = document.createElement('li');
        
        const link = document.createElement('a');
        link.href = article.url;
        link.textContent = article.title;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        
        const source = document.createElement('span');
        source.className = 'news-source';
        source.textContent = `(${article.source})`;
        
        li.appendChild(link);
        li.appendChild(source);
        newsList.appendChild(li);
      });
    } else {
      newsList.innerHTML = '<li style="text-align: center; color: #aaa;">No news articles available at the moment.</li>';
    }
    
  } catch (error) {
    console.error('Error fetching Telangana news:', error);
    
    if (newsLoading) {
      newsLoading.textContent = 'Failed to load news. Please try again later.';
    }
  }
}



// Format numbers with commas
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Smooth scroll to section
function scrollToSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Add smooth scroll to "View Live Homicide Trends" button
document.addEventListener('DOMContentLoaded', function() {
  const liveBtn = document.querySelector('.map-live-btn');
  if (liveBtn && liveBtn.getAttribute('href') === '#live-trends') {
    liveBtn.addEventListener('click', function(e) {
      e.preventDefault();
      scrollToSection('live-trends');
    });
  }
});