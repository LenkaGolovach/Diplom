<template>
  <div class="reports-container">
    <div class="reports-header">
      <h1>Отчёты</h1>
      <div class="reports-controls">
        <select v-model="selectedReportType" class="report-type-select">
          <option value="tasks">Отчёт по задачам</option>
          <option value="projects">Отчёт по проектам</option>
          <option value="members">Отчёт по участникам</option>
        </select>
        
        <div class="date-range">
          <input 
            type="date" 
            v-model="startDate" 
            class="date-input"
            placeholder="Начальная дата"
          >
          <input 
            type="date" 
            v-model="endDate" 
            class="date-input"
            placeholder="Конечная дата"
          >
        </div>
        
        <button @click="generateReport" class="generate-button">
          Сформировать отчёт
        </button>
        
        <button @click="exportReport" class="export-button" :disabled="!reportData">
          Экспорт в Excel
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      Загрузка данных...
    </div>

    <div v-else-if="reportData" class="report-content">
      <!-- Отчёт по задачам -->
      <div v-if="selectedReportType === 'tasks'" class="tasks-report">
        <h2>Отчёт по задачам</h2>
        <div class="report-summary">
          <div class="summary-item">
            <span class="label">Всего задач:</span>
            <span class="value">{{ reportData.totalTasks }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Выполнено:</span>
            <span class="value">{{ reportData.completedTasks }}</span>
          </div>
          <div class="summary-item">
            <span class="label">В процессе:</span>
            <span class="value">{{ reportData.inProgressTasks }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Не начато:</span>
            <span class="value">{{ reportData.notStartedTasks }}</span>
          </div>
        </div>

        <div class="tasks-list">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Проект</th>
                <th>Статус</th>
                <th>Приоритет</th>
                <th>Создана</th>
                <th>Завершена</th>
                <th>Участники</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="task in reportData.tasks" :key="task.id">
                <td>{{ task.name }}</td>
                <td>{{ task.project }}</td>
                <td>{{ task.status }}</td>
                <td>{{ task.priority }}</td>
                <td>{{ formatDate(task.created_at) }}</td>
                <td>{{ task.completed_at ? formatDate(task.completed_at) : '-' }}</td>
                <td>{{ task.members.join(', ') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Отчёт по проектам -->
      <div v-if="selectedReportType === 'projects'" class="projects-report">
        <h2>Отчёт по проектам</h2>
        <div class="report-summary">
          <div class="summary-item">
            <span class="label">Всего проектов:</span>
            <span class="value">{{ reportData.totalProjects }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Активных:</span>
            <span class="value">{{ reportData.activeProjects }}</span>
          </div>
          <div class="summary-item">
            <span class="label">Завершённых:</span>
            <span class="value">{{ reportData.completedProjects }}</span>
          </div>
        </div>

        <div class="projects-list">
          <table>
            <thead>
              <tr>
                <th>Название</th>
                <th>Статус</th>
                <th>Всего задач</th>
                <th>Выполнено</th>
                <th>В процессе</th>
                <th>Создан</th>
                <th>Участники</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="project in reportData.projects" :key="project.id">
                <td>{{ project.name }}</td>
                <td>{{ project.status }}</td>
                <td>{{ project.totalTasks }}</td>
                <td>{{ project.completedTasks }}</td>
                <td>{{ project.inProgressTasks }}</td>
                <td>{{ formatDate(project.created_at) }}</td>
                <td>{{ project.members.join(', ') }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Отчёт по участникам -->
      <div v-if="selectedReportType === 'members'" class="members-report">
        <h2>Отчёт по участникам</h2>
        <div class="report-summary">
          <div class="summary-item">
            <span class="label">Всего участников:</span>
            <span class="value">{{ reportData.totalMembers }}</span>
          </div>
        </div>

        <div class="members-list">
          <table>
            <thead>
              <tr>
                <th>Участник</th>
                <th>Всего задач</th>
                <th>Выполнено</th>
                <th>В процессе</th>
                <th>Проекты</th>
                <th>Последняя активность</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="member in reportData.members" :key="member.id">
                <td>{{ member.name }}</td>
                <td>{{ member.totalTasks }}</td>
                <td>{{ member.completedTasks }}</td>
                <td>{{ member.inProgressTasks }}</td>
                <td>{{ member.projects.join(', ') }}</td>
                <td>{{ formatDate(member.lastActivity) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-else class="no-data">
      Выберите тип отчёта и нажмите "Сформировать отчёт"
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import * as XLSX from 'xlsx';

export default {
  name: 'ReportsView',
  data() {
    return {
      selectedReportType: 'tasks',
      startDate: '',
      endDate: '',
      reportData: null,
      loading: false
    };
  },
  methods: {
    async generateReport() {
      this.loading = true;
      this.reportData = null;
      
      try {
        const params = {
          report_type: this.selectedReportType,
          start_date: this.startDate,
          end_date: this.endDate
        };
        
        const response = await axios.get('/api/reports/', {
          params,
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        this.reportData = response.data;
      } catch (error) {
        console.error('Ошибка при формировании отчёта:', error);
        alert('Произошла ошибка при формировании отчёта. Пожалуйста, попробуйте снова.');
      } finally {
        this.loading = false;
      }
    },
    
    exportReport() {
      if (!this.reportData) return;
      
      let data = [];
      let filename = '';
      
      switch (this.selectedReportType) {
        case 'tasks':
          data = this.reportData.tasks;
          filename = 'tasks_report';
          break;
        case 'projects':
          data = this.reportData.projects;
          filename = 'projects_report';
          break;
        case 'members':
          data = this.reportData.members;
          filename = 'members_report';
          break;
      }
      
      // Создаем рабочую книгу Excel
      const ws = XLSX.utils.json_to_sheet(data);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, 'Report');
      
      // Генерируем имя файла с датой
      const date = new Date().toISOString().split('T')[0];
      const fullFilename = `${filename}_${date}.xlsx`;
      
      // Скачиваем файл
      XLSX.writeFile(wb, fullFilename);
    },
    
    formatDate(dateString) {
      if (!dateString) return '-';
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU');
    }
  }
};
</script>

<style scoped>
.reports-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.reports-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.reports-controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.report-type-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.date-range {
  display: flex;
  gap: 10px;
}

.date-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.generate-button, .export-button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.generate-button {
  background-color: #0079bf;
  color: white;
}

.generate-button:hover {
  background-color: #005a8c;
}

.export-button {
  background-color: #f0f0f0;
  color: #333;
}

.export-button:hover {
  background-color: #e0e0e0;
}

.export-button:disabled {
  background-color: #f0f0f0;
  color: #999;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 20px;
  font-size: 16px;
  color: #666;
}

.no-data {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: #666;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.report-content {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.report-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.summary-item .label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.summary-item .value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f5f5f5;
  font-weight: 600;
  color: #333;
}

tr:hover {
  background-color: #f9f9f9;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
}
</style> 