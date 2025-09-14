// Инициализация Telegram WebApp
let tg = window.Telegram.WebApp;

// Инициализация приложения
document.addEventListener('DOMContentLoaded', function() {
    // Настройка Telegram WebApp
    tg.ready();
    tg.expand();
    
    // Установка цветовой схемы
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
    document.body.style.color = tg.themeParams.text_color || '#000000';
    
    // Инициализация приложения
    initializeApp();
});

// Основные функции навигации
function showMainMenu() {
    hideAllSections();
    document.getElementById('mainMenu').style.display = 'block';
}

function showSmartAutomation() {
    hideAllSections();
    document.getElementById('smartAutomation').style.display = 'block';
}

function showRecordingAutomation() {
    hideAllSections();
    document.getElementById('recordingAutomation').style.display = 'block';
}

function showPlatforms() {
    hideAllSections();
    document.getElementById('platforms').style.display = 'block';
}

function showNotifications() {
    hideAllSections();
    document.getElementById('notifications').style.display = 'block';
}

function showTemplates() {
    hideAllSections();
    document.getElementById('templates').style.display = 'block';
    loadTemplates();
}

function showSettings() {
    hideAllSections();
    document.getElementById('settings').style.display = 'block';
    loadSettings();
}

function hideAllSections() {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    document.getElementById('mainMenu').style.display = 'none';
}

// Умная автоматизация
function startSmartAutomation() {
    const formData = collectSmartFormData();
    
    if (!validateSmartForm(formData)) {
        return;
    }
    
    showStatus('Создание объявлений...', '⏳');
    
    // Отправка данных на сервер
    sendToBot('smart_automation', formData)
        .then(response => {
            hideStatus();
            if (response.success) {
                showNotification('Объявления успешно созданы!', 'success');
                showMainMenu();
            } else {
                showNotification('Ошибка: ' + response.error, 'error');
            }
        })
        .catch(error => {
            hideStatus();
            showNotification('Ошибка соединения: ' + error.message, 'error');
        });
}

function collectSmartFormData() {
    return {
        email: document.getElementById('smartEmail').value,
        password: document.getElementById('smartPassword').value,
        hotel_name: document.getElementById('smartHotelName').value,
        hotel_address: document.getElementById('smartHotelAddress').value,
        hotel_type: document.getElementById('smartHotelType').value,
        city: document.getElementById('smartCity').value,
        phone: document.getElementById('smartPhone').value,
        website: document.getElementById('smartWebsite').value,
        contact_name: document.getElementById('smartContactName').value,
        contact_email: document.getElementById('smartContactEmail').value,
        description: document.getElementById('smartDescription').value,
        amenities: document.getElementById('smartAmenities').value,
        platforms: {
            ostrovok: document.getElementById('platformOstrovok').checked,
            bronevik: document.getElementById('platformBronevik').checked,
            '101hotels': document.getElementById('platform101Hotels').checked
        }
    };
}

function validateSmartForm(data) {
    const required = ['email', 'password', 'hotel_name', 'hotel_address', 'hotel_type', 'city', 'phone', 'contact_name', 'contact_email'];
    
    for (const field of required) {
        if (!data[field] || data[field].trim() === '') {
            showNotification(`Поле "${getFieldLabel(field)}" обязательно для заполнения`, 'error');
            return false;
        }
    }
    
    // Проверка email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.email)) {
        showNotification('Неверный формат email', 'error');
        return false;
    }
    
    // Проверка контактного email
    if (!emailRegex.test(data.contact_email)) {
        showNotification('Неверный формат контактного email', 'error');
        return false;
    }
    
    // Проверка выбора платформ
    const hasPlatform = Object.values(data.platforms).some(selected => selected);
    if (!hasPlatform) {
        showNotification('Выберите хотя бы одну платформу', 'error');
        return false;
    }
    
    return true;
}

function getFieldLabel(field) {
    const labels = {
        email: 'Email',
        password: 'Пароль',
        hotel_name: 'Название отеля',
        hotel_address: 'Адрес отеля',
        hotel_type: 'Тип отеля',
        city: 'Город',
        phone: 'Телефон',
        contact_name: 'Контактное лицо',
        contact_email: 'Контактный email'
    };
    return labels[field] || field;
}

// Запись действий
function showRecordActions() {
    showNotification('Функция записи действий будет доступна в следующей версии', 'warning');
}

function showPlayActions() {
    showNotification('Функция воспроизведения действий будет доступна в следующей версии', 'warning');
}

// Платформы
function openPlatform(platform) {
    const platformNames = {
        ostrovok: 'Ostrovok',
        bronevik: 'Bronevik',
        '101hotels': '101 Hotels'
    };
    
    showNotification(`Открытие ${platformNames[platform]}...`, 'info');
    
    // Отправка команды боту для открытия платформы
    sendToBot('open_platform', { platform: platform })
        .then(response => {
            if (response.success) {
                showNotification(`${platformNames[platform]} открыт в браузере`, 'success');
            } else {
                showNotification('Ошибка открытия платформы', 'error');
            }
        })
        .catch(error => {
            showNotification('Ошибка соединения', 'error');
        });
}

// Настройки уведомлений
function saveNotificationSettings() {
    const settings = {
        bookingNotifications: document.getElementById('bookingNotifications').checked,
        statusNotifications: document.getElementById('statusNotifications').checked,
        errorNotifications: document.getElementById('errorNotifications').checked
    };
    
    sendToBot('save_notification_settings', settings)
        .then(response => {
            if (response.success) {
                showNotification('Настройки уведомлений сохранены', 'success');
            } else {
                showNotification('Ошибка сохранения настроек', 'error');
            }
        })
        .catch(error => {
            showNotification('Ошибка соединения', 'error');
        });
}

// Шаблоны
function loadTemplates() {
    sendToBot('get_templates', {})
        .then(response => {
            if (response.success) {
                displayTemplates(response.templates);
            } else {
                showNotification('Ошибка загрузки шаблонов', 'error');
            }
        })
        .catch(error => {
            showNotification('Ошибка соединения', 'error');
        });
}

function displayTemplates(templates) {
    const container = document.getElementById('templatesList');
    
    if (templates.length === 0) {
        container.innerHTML = '<div class="template-item"><p>Шаблоны не найдены</p></div>';
        return;
    }
    
    container.innerHTML = templates.map(template => `
        <div class="template-item">
            <div class="template-header">
                <div class="template-name">${template.name}</div>
                <div class="template-date">${formatDate(template.created_at)}</div>
            </div>
            <div class="template-info">
                <p><strong>Платформа:</strong> ${template.platform}</p>
                <p><strong>Действий:</strong> ${template.actions_count}</p>
            </div>
            <div class="template-actions">
                <button class="template-btn" onclick="playTemplate('${template.id}')">▶️ Воспроизвести</button>
                <button class="template-btn secondary" onclick="deleteTemplate('${template.id}')">🗑️ Удалить</button>
            </div>
        </div>
    `).join('');
}

function playTemplate(templateId) {
    showStatus('Воспроизведение шаблона...', '⏳');
    
    sendToBot('play_template', { template_id: templateId })
        .then(response => {
            hideStatus();
            if (response.success) {
                showNotification('Шаблон успешно воспроизведен', 'success');
            } else {
                showNotification('Ошибка воспроизведения: ' + response.error, 'error');
            }
        })
        .catch(error => {
            hideStatus();
            showNotification('Ошибка соединения', 'error');
        });
}

function deleteTemplate(templateId) {
    if (confirm('Вы уверены, что хотите удалить этот шаблон?')) {
        sendToBot('delete_template', { template_id: templateId })
            .then(response => {
                if (response.success) {
                    showNotification('Шаблон удален', 'success');
                    loadTemplates();
                } else {
                    showNotification('Ошибка удаления', 'error');
                }
            })
            .catch(error => {
                showNotification('Ошибка соединения', 'error');
            });
    }
}

// Настройки
function loadSettings() {
    sendToBot('get_settings', {})
        .then(response => {
            if (response.success) {
                document.getElementById('bnovoApiKey').value = response.settings.bnovo_api_key || '';
                document.getElementById('debugMode').checked = response.settings.debug_mode || false;
            }
        })
        .catch(error => {
            console.error('Ошибка загрузки настроек:', error);
        });
}

function saveSettings() {
    const settings = {
        bnovo_api_key: document.getElementById('bnovoApiKey').value,
        debug_mode: document.getElementById('debugMode').checked
    };
    
    sendToBot('save_settings', settings)
        .then(response => {
            if (response.success) {
                showNotification('Настройки сохранены', 'success');
            } else {
                showNotification('Ошибка сохранения настроек', 'error');
            }
        })
        .catch(error => {
            showNotification('Ошибка соединения', 'error');
        });
}

// Статус операций
function showStatus(text, icon = '⏳') {
    document.getElementById('statusText').textContent = text;
    document.getElementById('statusOverlay').style.display = 'flex';
}

function hideStatus() {
    document.getElementById('statusOverlay').style.display = 'none';
}

// Уведомления
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Отправка данных боту
function sendToBot(command, data) {
    return new Promise((resolve, reject) => {
        // В реальном приложении здесь будет отправка данных на ваш сервер
        // Для демонстрации используем симуляцию
        
        setTimeout(() => {
            // Симуляция успешного ответа
            resolve({
                success: true,
                data: data
            });
        }, 2000);
        
        // Для реальной интеграции используйте:
        /*
        fetch('/api/bot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                command: command,
                data: data,
                user_id: tg.initDataUnsafe.user?.id
            })
        })
        .then(response => response.json())
        .then(resolve)
        .catch(reject);
        */
    });
}

// Утилиты
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function initializeApp() {
    // Инициализация приложения
    console.log('Hotel Bot Mini App инициализирован');
    
    // Загрузка начальных данных
    loadTemplates();
    loadSettings();
    
    // Настройка обработчиков событий
    setupEventHandlers();
}

function setupEventHandlers() {
    // Обработчики для сохранения настроек уведомлений
    const notificationCheckboxes = document.querySelectorAll('#notifications input[type="checkbox"]');
    notificationCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', saveNotificationSettings);
    });
    
    // Обработчики для кнопок закрытия уведомлений
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('notification')) {
            e.target.remove();
        }
    });
}

// Обработка кнопки "Назад" в Telegram
tg.onEvent('backButtonClicked', function() {
    if (document.getElementById('mainMenu').style.display === 'none') {
        showMainMenu();
    } else {
        tg.close();
    }
});

// Показываем кнопку "Назад" когда не на главном экране
function updateBackButton() {
    if (document.getElementById('mainMenu').style.display === 'none') {
        tg.BackButton.show();
    } else {
        tg.BackButton.hide();
    }
}

// Обновляем кнопку "Назад" при смене экранов
const originalShowMainMenu = showMainMenu;
showMainMenu = function() {
    originalShowMainMenu();
    updateBackButton();
};

const originalShowSmartAutomation = showSmartAutomation;
showSmartAutomation = function() {
    originalShowSmartAutomation();
    updateBackButton();
};

const originalShowRecordingAutomation = showRecordingAutomation;
showRecordingAutomation = function() {
    originalShowRecordingAutomation();
    updateBackButton();
};

const originalShowPlatforms = showPlatforms;
showPlatforms = function() {
    originalShowPlatforms();
    updateBackButton();
};

const originalShowNotifications = showNotifications;
showNotifications = function() {
    originalShowNotifications();
    updateBackButton();
};

const originalShowTemplates = showTemplates;
showTemplates = function() {
    originalShowTemplates();
    updateBackButton();
};

const originalShowSettings = showSettings;
showSettings = function() {
    originalShowSettings();
    updateBackButton();
};
