// === КОНФИГУРАЦИЯ ===
const CONFIG = {
    backendUrl: 'http://localhost:8000',
    refreshInterval: 300000, // 5 минут
    demoMode: false
};

// Глобальные переменные
let currentMap = null;
let forecastChart = null;
let currentTab = 'dashboard';

// === 1. УПРАВЛЕНИЕ ВКЛАДКАМИ ===
function initTabs() {
    console.log('Инициализация вкладок...');
    
    // Обработчики для вкладок в меню
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const tabId = this.getAttribute('data-tab');
            console.log('Переключение на вкладку:', tabId);
            
            switchTab(tabId, this);
        });
    });
    
    // Обработчик для кнопки обновления погоды
    document.getElementById('refreshWeatherBtn')?.addEventListener('click', fetchCurrentWeather);
    
    // Обработчик для слайдера прогноза
    const forecastRange = document.getElementById('forecastRange');
    const rangeValue = document.getElementById('rangeValue');
    if (forecastRange && rangeValue) {
        forecastRange.addEventListener('input', function() {
            rangeValue.textContent = `${this.value} часов`;
        });
    }
    
    // Обработчик для кнопки моделирования
    document.getElementById('startSimulationBtn')?.addEventListener('click', startSimulation);
    
    // Обработчик для экспорта CSV
    document.getElementById('exportBtn')?.addEventListener('click', () => {
        alert('Экспорт CSV выполнен!\nФайл сохранен в папке загрузок.');
    });
    
    // Обработчик для отправки оповещения
    document.getElementById('sendAlertBtn')?.addEventListener('click', () => {
        const type = document.getElementById('alertType').value;
        const level = document.getElementById('alertLevel').value;
        alert(`Оповещение "${type}" (${level}) отправлено в службу спасения!`);
    });
    
    // Обработчик для обновления прогноза
    document.getElementById('refreshForecastBtn')?.addEventListener('click', load5DayForecast);
    document.getElementById('forecastCity')?.addEventListener('change', load5DayForecast);
    
    // Обработчик для периода архива
    document.getElementById('archivePeriod')?.addEventListener('change', fetchArchiveData);
}

// Функция переключения вкладок
function switchTab(tabId, element = null) {
    console.log('switchTab вызван с:', tabId);
    
    // Обновляем активную вкладку
    currentTab = tabId;
    
    // Скрываем все разделы
    document.querySelectorAll('.view-section').forEach(section => {
        section.classList.remove('active-view');
    });
    
    // Показываем выбранный раздел
    const targetSection = document.getElementById(tabId);
    if (targetSection) {
        targetSection.classList.add('active-view');
    } else {
        console.error('Раздел не найден:', tabId);
        return;
    }
    
    // Обновляем активный пункт меню
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    if (element) {
        element.classList.add('active');
    } else {
        // Находим соответствующий элемент меню
        const menuItem = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
        if (menuItem) menuItem.classList.add('active');
    }
    
    // Обновляем заголовок
    const titles = {
        'dashboard': 'Оперативный мониторинг',
        'modeling': 'Численное моделирование (NWP)',
        'archive': 'Архив метеоданных',
        'alerts': 'Управление оповещениями',
        'forecast': 'Прогноз на 5 дней'
    };
    
    document.getElementById('page-title').textContent = titles[tabId] || 'Метео система';
    
    // Если переключили на карту - обновляем её размер
    if (tabId === 'dashboard' && currentMap) {
        setTimeout(() => {
            currentMap.invalidateSize();
        }, 100);
    }
    
    // Загружаем данные для вкладки
    setTimeout(() => {
        switch(tabId) {
            case 'archive':
                fetchArchiveData();
                break;
            case 'alerts':
                fetchAlerts();
                break;
            case 'forecast':
                load5DayForecast();
                break;
            case 'dashboard':
                if (!currentMap) initMap();
                break;
        }
    }, 200);
}

// === 2. ИНИЦИАЛИЗАЦИЯ КАРТЫ ===
function initMap() {
    console.log('Инициализация карты...');
    
    if (!document.getElementById('map')) {
        console.error('Элемент карты не найден!');
        return;
    }
    
    // Создаем карту
    currentMap = L.map('map', {
        zoomControl: false,
        attributionControl: false
    }).setView([53.92, 27.50], 11);
    
    // Добавляем слой карты
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(currentMap);
    
    // Иконка для метеостанций
    const stationIcon = L.divIcon({
        className: 'custom-div-icon',
        html: '<div style="background-color:#3b82f6; width:12px; height:12px; border-radius:50%; border:2px solid white; box-shadow: 0 0 10px #3b82f6;"></div>',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
    });
    
    // Добавляем метеостанции
    L.marker([53.94, 27.69], { icon: stationIcon })
     .addTo(currentMap)
     .bindPopup('<strong>МС Уручье</strong><br>ID: 26850<br>Температура: 19.2°C');
    
    L.marker([53.86, 27.50], { icon: stationIcon })
     .addTo(currentMap)
     .bindPopup('<strong>МС Курасовщина</strong><br>ID: 26851<br>Температура: 18.8°C');
    
    // Добавляем анимацию облаков
    addCloudAnimation();
    
    console.log('Карта инициализирована');
}

// Анимация облаков
function addCloudAnimation() {
    if (!currentMap) return;
    
    // Дождевое облако
    const rainBounds = [[53.85, 27.40], [54.00, 27.70]];
    const rainSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    rainSvg.setAttribute('viewBox', "0 0 200 200");
    rainSvg.innerHTML = `
        <defs>
            <linearGradient id="rainGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.4" />
                <stop offset="100%" style="stop-color:#1e40af;stop-opacity:0.2" />
            </linearGradient>
        </defs>
        <path style="fill:url('#rainGradient'); opacity: 0.8;" 
              d="M 50 100 Q 70 70 100 85 Q 130 60 150 90 Q 170 120 130 140 Q 90 150 60 130 Q 30 120 50 100 Z" />
    `;
    
    L.svgOverlay(rainSvg, rainBounds, { opacity: 0.9 })
     .addTo(currentMap)
     .bindPopup('<strong>Зона осадков</strong><br>Интенсивность: Умеренная');
    
    // Грозовое облако
    const stormBounds = [[53.80, 27.10], [54.05, 27.55]];
    const stormSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    stormSvg.setAttribute('viewBox', "0 0 200 200");
    stormSvg.innerHTML = `
        <defs>
            <radialGradient id="stormGradient">
                <stop offset="0%" style="stop-color:rgb(220, 38, 38);stop-opacity:0.6" />
                <stop offset="100%" style="stop-color:rgb(185, 28, 28);stop-opacity:0" />
            </radialGradient>
        </defs>
        <path style="fill:url('#stormGradient');" 
              d="M 50 100 Q 70 60 100 80 Q 140 50 160 90 Q 180 130 140 150 Q 100 170 60 140 Q 30 130 50 100 Z" />
    `;
    
    L.svgOverlay(stormSvg, stormBounds, { opacity: 0.8 })
     .addTo(currentMap)
     .bindPopup('<strong>Грозовой фронт</strong><br>Интенсивность: Высокая');
}

// === 3. ЗАГРУЗКА ДАННЫХ ===
async function fetchCurrentWeather() {
    console.log('Загрузка текущей погоды...');
    
    const refreshIcon = document.getElementById('refreshIcon');
    if (refreshIcon) {
        refreshIcon.classList.add('refreshing');
    }
    
    try {
        // Пробуем получить данные с бэкенда
        const response = await fetch(`${CONFIG.backendUrl}/api/current-weather?station_id=26850`);
        
        let weatherData;
        if (response.ok) {
            weatherData = await response.json();
            CONFIG.demoMode = false;
        } else {
            // Используем демо-данные
            weatherData = getDemoWeatherData();
            CONFIG.demoMode = true;
        }
        
        updateWeatherUI(weatherData);
        updateLastUpdateTime();
        
        if (CONFIG.demoMode) {
            showDemoMessage('Демо-режим: Используются тестовые данные');
        }
        
    } catch (error) {
        console.error('Ошибка загрузки погоды:', error);
        updateWeatherUI(getDemoWeatherData());
        updateLastUpdateTime();
        showDemoMessage('Ошибка соединения. Используются демо-данные');
    } finally {
        if (refreshIcon) {
            setTimeout(() => {
                refreshIcon.classList.remove('refreshing');
            }, 1000);
        }
    }
}

function getDemoWeatherData() {
    return {
        temperature: 19.2,
        feels_like: 18.5,
        pressure: 748,
        humidity: 65,
        wind_speed: 12,
        wind_direction: "СЗ",
        description: "Облачно с прояснениями"
    };
}

function updateWeatherUI(data) {
    // Температура
    const tempElement = document.getElementById('currentTemp');
    if (tempElement && data.temperature !== undefined) {
        tempElement.textContent = `${data.temperature > 0 ? '+' : ''}${data.temperature}°C`;
        updateTempColor(tempElement, data.temperature);
    }
    
    // Давление
    const pressureElement = document.getElementById('currentPressure');
    if (pressureElement && data.pressure !== undefined) {
        pressureElement.textContent = `${Math.round(data.pressure)} мм`;
    }
    
    // Ветер
    const windElement = document.getElementById('currentWind');
    if (windElement && data.wind_speed !== undefined) {
        const direction = data.wind_direction || "СЗ";
        windElement.textContent = `${direction}, ${data.wind_speed} м/с`;
    }
    
    // Влажность
    const humidityElement = document.getElementById('currentHumidity');
    if (humidityElement && data.humidity !== undefined) {
        humidityElement.textContent = `${data.humidity}%`;
    }
    
    // Ощущаемая температура
    const feelsLikeElement = document.getElementById('feelsLike');
    if (feelsLikeElement && data.feels_like !== undefined) {
        feelsLikeElement.textContent = `${data.feels_like > 0 ? '+' : ''}${data.feels_like}°C`;
        updateTempColor(feelsLikeElement, data.feels_like);
    }
}

function updateTempColor(element, temp) {
    element.classList.remove('temp-hot', 'temp-warm', 'temp-mild', 'temp-cool', 'temp-cold');
    
    if (temp >= 30) element.classList.add('temp-hot');
    else if (temp >= 20) element.classList.add('temp-warm');
    else if (temp >= 10) element.classList.add('temp-mild');
    else if (temp >= 0) element.classList.add('temp-cool');
    else element.classList.add('temp-cold');
}

function updateLastUpdateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('ru-RU', { 
        hour: '2-digit', 
        minute: '2-digit'
    });
    
    const dateString = now.toLocaleDateString('ru-RU');
    
    let timeElement = document.querySelector('.last-update');
    if (!timeElement) {
        const cardHeader = document.querySelector('.card .card-header');
        if (!cardHeader) return;
        
        timeElement = document.createElement('div');
        timeElement.className = 'last-update';
        timeElement.style.cssText = `
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 5px;
            font-family: 'Courier New', monospace;
        `;
        cardHeader.appendChild(timeElement);
    }
    
    timeElement.textContent = `Обновлено: ${dateString} ${timeString}`;
}

function showDemoMessage(message) {
    const card = document.querySelector('#dashboard .card:last-child');
    if (!card) return;
    
    const existing = card.querySelector('.demo-warning');
    if (existing) existing.remove();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'demo-warning';
    messageDiv.style.cssText = `
        background: rgba(245, 158, 11, 0.2);
        border-left: 3px solid var(--warning);
        padding: 10px;
        margin: 10px 20px;
        border-radius: 4px;
        font-size: 12px;
        color: var(--text-main);
    `;
    messageDiv.innerHTML = `
        <i class="fa-solid fa-info-circle"></i> 
        <strong>${message}</strong>
    `;
    
    card.insertBefore(messageDiv, card.firstChild);
}

// === 4. АРХИВНЫЕ ДАННЫЕ ===
async function fetchArchiveData() {
    try {
        const period = document.getElementById('archivePeriod')?.value || '24';
        const tbody = document.getElementById('archiveTableBody');
        
        if (!tbody) return;
        
        // Показываем загрузку
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 20px; color: var(--text-muted);">
                    <i class="fa-solid fa-spinner fa-spin"></i> Загрузка данных...
                </td>
            </tr>
        `;
        
        // Имитация загрузки
        setTimeout(() => {
            updateArchiveTable(getDemoArchiveData());
        }, 800);
        
    } catch (error) {
        console.error('Ошибка загрузки архива:', error);
    }
}

function getDemoArchiveData() {
    const now = new Date();
    const data = [];
    
    for (let i = 0; i < 5; i++) {
        const time = new Date(now.getTime() - i * 3600000);
        const temp = 18 + Math.random() * 3 - 1.5;
        
        data.push({
            timestamp: time.toISOString(),
            temperature: temp,
            humidity: 60 + Math.random() * 20,
            pressure: 745 + Math.random() * 10,
            wind_speed: (5 + Math.random() * 10).toFixed(1),
            wind_direction: ['С', 'СВ', 'В', 'ЮВ', 'Ю', 'ЮЗ', 'З', 'СЗ'][Math.floor(Math.random() * 8)],
            description: temp > 20 ? 'Ясно' : temp > 15 ? 'Облачно' : 'Пасмурно'
        });
    }
    
    return data;
}

function updateArchiveTable(data) {
    const tbody = document.getElementById('archiveTableBody');
    if (!tbody || !Array.isArray(data)) return;
    
    tbody.innerHTML = '';
    
    data.forEach(item => {
        const row = document.createElement('tr');
        const date = new Date(item.timestamp);
        const dateStr = date.toLocaleDateString('ru-RU') + ' ' + 
                       date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        
        // Определяем статус
        let statusClass = 'tag-ok';
        let statusText = 'Норма';
        
        if (item.temperature > 30 || item.temperature < -15) {
            statusClass = 'tag-crit';
            statusText = 'Опасно';
        } else if (item.temperature > 25 || item.temperature < -10) {
            statusClass = 'tag-warn';
            statusText = 'Внимание';
        }
        
        // Иконка погоды
        let weatherIcon = 'fa-cloud';
        if (item.description?.includes('ясн')) weatherIcon = 'fa-sun';
        if (item.description?.includes('дожд')) weatherIcon = 'fa-cloud-rain';
        
        row.innerHTML = `
            <td>${dateStr}</td>
            <td>${item.temperature > 0 ? '+' : ''}${item.temperature.toFixed(1)}°C</td>
            <td>${Math.round(item.humidity)}%</td>
            <td>${Math.round(item.pressure)} мм</td>
            <td>${item.wind_direction}, ${item.wind_speed} м/с</td>
            <td><i class="fa-solid ${weatherIcon}"></i> ${item.description}</td>
            <td><span class="status-tag ${statusClass}">${statusText}</span></td>
        `;
        
        tbody.appendChild(row);
    });
}

// === 5. ОПОВЕЩЕНИЯ ===
async function fetchAlerts() {
    try {
        const container = document.getElementById('alertsContainer');
        if (!container) return;
        
        // Показываем загрузку
        container.innerHTML = `
            <div style="text-align: center; padding: 20px; color: var(--text-muted);">
                <i class="fa-solid fa-spinner fa-spin"></i> Загрузка оповещений...
            </div>
        `;
        
        // Имитация загрузки
        setTimeout(() => {
            updateAlertsUI(getDemoAlertsData());
        }, 800);
        
    } catch (error) {
        console.error('Ошибка загрузки оповещений:', error);
    }
}

function getDemoAlertsData() {
    return [
        {
            id: 1,
            level: 'critical',
            type: 'storm',
            title: 'Грозовой фронт',
            description: 'Ожидается прохождение фронта через Минск. Гроза, шквал до 25 м/с.',
            location: 'Минский район',
            valid_until: new Date(Date.now() + 3600000).toISOString()
        },
        {
            id: 2,
            level: 'warning',
            type: 'fog',
            title: 'Туман',
            description: 'Видимость менее 200 метров на трассе М1',
            location: 'Трасса М1 (участок аэропорт)',
            valid_until: new Date(Date.now() + 7200000).toISOString()
        }
    ];
}

function updateAlertsUI(alerts) {
    const container = document.getElementById('alertsContainer');
    if (!container || !Array.isArray(alerts)) return;
    
    container.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = `alert-item ${alert.level === 'critical' ? 'alert-crit' : 'alert-warn'}`;
        
        const icon = alert.level === 'critical' ? 'fa-bolt' : 'fa-triangle-exclamation';
        const levelText = alert.level === 'critical' ? 'КРАСНЫЙ' : 'ОРАНЖЕВЫЙ';
        const color = alert.level === 'critical' ? 'var(--danger)' : 'var(--warning)';
        
        const validUntil = new Date(alert.valid_until).toLocaleString('ru-RU');
        
        alertElement.innerHTML = `
            <div>
                <div style="font-weight: bold; color: ${color}; font-size: 14px; margin-bottom: 4px;">
                    <i class="fa-solid ${icon}"></i> ${levelText}: ${alert.title}
                </div>
                <div style="font-size: 12px; color: var(--text-muted);">
                    ${alert.description}<br>
                    <small>Локация: ${alert.location}</small><br>
                    <small>Действует до: ${validUntil}</small>
                </div>
            </div>
            <button class="btn btn-sm" onclick="showAlertDetails(${alert.id})">Детали</button>
        `;
        
        container.appendChild(alertElement);
    });
}

// === 6. ПРОГНОЗ НА 5 ДНЕЙ ===
async function load5DayForecast() {
    try {
        const container = document.getElementById('forecastContainer');
        if (!container) return;
        
        // Показываем загрузку
        container.innerHTML = `
            <div style="text-align: center; padding: 20px; color: var(--text-muted); grid-column: 1 / -1;">
                <i class="fa-solid fa-spinner fa-spin"></i> Загрузка прогноза...
            </div>
        `;
        
        // Имитация загрузки
        setTimeout(() => {
            updateForecastUI(getDemoForecastData());
        }, 1000);
        
    } catch (error) {
        console.error('Ошибка загрузки прогноза:', error);
    }
}

function getDemoForecastData() {
    const now = new Date();
    const forecast = [];
    
    for (let i = 1; i <= 5; i++) {
        const date = new Date(now.getTime() + i * 86400000);
        const temp = 15 + Math.random() * 8;
        
        forecast.push({
            date: date,
            temperature: Math.round(temp),
            humidity: 60 + Math.random() * 25,
            description: temp > 20 ? 'Ясно' : temp > 15 ? 'Облачно' : 'Пасмурно',
            icon: temp > 20 ? '01d' : temp > 15 ? '03d' : '04d'
        });
    }
    
    return forecast;
}

function updateForecastUI(forecast) {
    const container = document.getElementById('forecastContainer');
    if (!container || !Array.isArray(forecast)) return;
    
    let html = '';
    
    forecast.forEach(day => {
        const dateStr = day.date.toLocaleDateString('ru-RU', { 
            weekday: 'short', 
            day: 'numeric',
            month: 'short'
        });
        
        const weatherIcon = getWeatherIcon(day.icon);
        const tempClass = getTempClass(day.temperature);
        
        html += `
            <div class="forecast-day">
                <div class="forecast-date">${dateStr}</div>
                <div class="weather-icon">${weatherIcon}</div>
                <div class="forecast-temp ${tempClass}">${day.temperature > 0 ? '+' : ''}${day.temperature}°C</div>
                <div class="forecast-desc">${day.description}</div>
                <div style="font-size: 11px; color: var(--text-muted); margin-top: 8px;">
                    Влажность: ${Math.round(day.humidity)}%
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function getWeatherIcon(iconCode) {
    const icons = {
        '01d': '☀️', '01n': '🌙',
        '02d': '⛅', '02n': '☁️',
        '03d': '☁️', '03n': '☁️',
        '04d': '☁️', '04n': '☁️',
        '09d': '🌧️', '09n': '🌧️',
        '10d': '🌦️', '10n': '🌧️',
        '11d': '⛈️', '11n': '⛈️',
        '13d': '❄️', '13n': '❄️',
        '50d': '🌫️', '50n': '🌫️'
    };
    return icons[iconCode] || '☁️';
}

// === 7. ГРАФИК ПРОГНОЗА ===
function initForecastChart() {
    const ctx = document.getElementById('forecastChart');
    if (!ctx) return null;
    
    return new Chart(ctx.getContext('2d'), {
        type: 'line',
        data: {
            labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
            datasets: [{
                label: 'Температура (°C)',
                data: [12, 11, 10, 14, 18, 19, 17, 15],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { 
                    ticks: { color: '#94a3b8' }, 
                    grid: { color: '#334155' }
                },
                y: { 
                    ticks: { color: '#94a3b8' }, 
                    grid: { color: '#334155' }
                }
            }
        }
    });
}

// === 8. МОДЕЛИРОВАНИЕ ===
function startSimulation() {
    const consoleDiv = document.getElementById('console');
    const btn = document.getElementById('startSimulationBtn');
    if (!consoleDiv || !btn) return;
    
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Вычисление...';
    btn.disabled = true;
    
    const logs = [
        "Инициализация модели WRF-ARW...",
        "Загрузка граничных условий...",
        "Декомпозиция сетки...",
        "Инициализация физических параметров...",
        "Итерация 1/100...",
        "Итерация 50/100...",
        "Итерация 100/100...",
        "УСПЕХ: Прогноз сгенерирован за 2.3с"
    ];
    
    consoleDiv.innerHTML = '';
    let i = 0;
    
    const interval = setInterval(() => {
        const time = new Date().toLocaleTimeString('ru-RU');
        consoleDiv.innerHTML += `<div class="log-line"><span class="log-time">${time}</span>${logs[i]}</div>`;
        consoleDiv.scrollTop = consoleDiv.scrollHeight;
        i++;
        
        if (i >= logs.length) {
            clearInterval(interval);
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Запустить расчёт';
            btn.disabled = false;
            
            // Обновляем график
            if (forecastChart) {
                forecastChart.data.datasets[0].data = forecastChart.data.datasets[0].data.map(v => 
                    v + (Math.random() * 2 - 1)
                );
                forecastChart.update();
            }
            
            // Показываем уведомление
            alert('Моделирование завершено успешно!');
        }
    }, 800);
}

// === 9. ИНИЦИАЛИЗАЦИЯ ПРИ ЗАГРУЗКЕ ===
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Метео система запускается...');
    
    // Инициализация вкладок
    initTabs();
    
    // Инициализация графика
    forecastChart = initForecastChart();
    
    // Загрузка начальных данных
    fetchCurrentWeather();
    
    // Автообновление каждые 5 минут
    setInterval(fetchCurrentWeather, CONFIG.refreshInterval);
    
    // Инициализация карты при первом показе дашборда
    setTimeout(() => {
        if (currentTab === 'dashboard') {
            initMap();
        }
    }, 500);
    
    console.log('✅ Система инициализирована');
});

// === 10. ГЛОБАЛЬНЫЕ ФУНКЦИИ ===
window.showAlertDetails = function(id) {
    alert(`Детали оповещения #${id}\nФункция в разработке`);
};