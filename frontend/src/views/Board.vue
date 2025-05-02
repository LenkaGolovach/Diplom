<template>
  <div class="board">
    <div class="board-header">
      <div class="board-title-wrapper">
        <div
          v-if="!isEditingBoardName"
          class="board-title"
          @dblclick="startEditingBoardName"
        >
          {{ truncatedBoardName }}
        </div>
        <input
          v-else
          ref="boardNameInput"
          v-model="board.name"
          @blur="stopEditingBoardName"
          @keyup.enter="stopEditingBoardName"
          class="board-title-input"
        />
        <button @click="showMembersModal = true" class="members-button">
          👥 Участники
        </button>
        <button @click="generateBoardReport" class="report-button">
          <i class="fas fa-chart-bar"></i> Отчёт по проекту
        </button>
      </div>
    </div>

    <div class="columns-container">
      <div class="columns">
        <Column
          v-for="(column, index) in board.columns"
          :key="column.id"
          :column="column"
          @add-task="addTask(index)"
          @delete-column="deleteColumn(index)"
          @update-column="updateColumn"
          @update-tasks="updateColumnTasks(index, $event)"
          @openTaskModal="openModal"
        />
      </div>
      <button class="add-column-button" @click="addColumn">
        + Добавить колонку
      </button>
    </div>

    <TaskModal
      v-if="showModal"
      :task="currentTask"
      @close="closeModal"
      @saveTask="saveTask"
    />

    <BoardMembersModal
      v-if="showMembersModal"
      :board="board"
      :current-user="currentUser"
      @close="showMembersModal = false"
      @update-members="fetchBoardData"
    />
  </div>
</template>

<script>
import Column from '../components/Column.vue';
import BoardMembersModal from '../components/BoardMembersModal.vue'
import TaskModal from '../components/TaskModal.vue';
import axios from 'axios';
import { reactive } from 'vue';
import Vue from 'vue';
import * as XLSX from 'xlsx';

const COLORS = [
  '#61bd4f', '#f2d600', 
  '#ff9f1a', '#eb5a46', 
  '#c377e0', '#0079bf'
];

export default {
  components: {
    Column,
    TaskModal,
    BoardMembersModal
  },
  props: {
    id: {
      type: [String, Number],
      required: true,
    },
  },
  data() {
    return {
      board: reactive({
        name: '',
        columns: [],
      }),
      showModal: false,
      currentTask: {
        id: null,
        name: '',
        description: '',
        subtasks: [],
        files: [],
      },
      currentColumnIndex: null,
      isEditingBoardName: false,
      showMembersModal: false,
      currentUser: null
    };
  },
  computed: {
    truncatedBoardName() {
      return this.board.name.length > 20 
        ? this.board.name.substring(0, 17) + '...' 
        : this.board.name
    }
  },
  watch: {
    // Добавляем наблюдатель за параметрами URL
    '$route.query': {
      handler(query) {
        if (query.task) {
          this.openTaskFromQuery(query.task);
        }
      },
      immediate: true
    }
  },
  async created() {
    console.log('Board component created with id:', this.id)
    await this.fetchUser();
    await this.fetchBoardData();
  },
  methods: {
    async fetchUser() {
      try {
        const response = await axios.get('/api/users/me/', {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        })
        this.currentUser = response.data
      } catch (error) {
        console.error('Ошибка загрузки пользователя:', error)
      }
    },
    async fetchBoardData() {
      try {
        console.log('Fetching board data for id:', this.id)
        const response = await axios.get(`/api/boards/${this.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          params: {
            include_tasks: true
          }
        });
        console.log('Board data received:', response.data)
        // Гарантируем наличие массива columns
        this.board = {
          ...response.data,
          columns: response.data.columns.map(column => ({
            ...column,
            tasks: column.tasks || []
          }))
        };
        
        // Инициализируем задачи для каждой колонки
        this.board.columns.forEach(col => {
          col.tasks = col.tasks || [];
        });
      } catch (error) {
        console.error('Ошибка загрузки доски:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
      }
    },
    async saveBoard() {
      try {
        await axios.put(`/api/boards/${this.id}/`, this.board, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
      } catch (error) {
        console.error('Ошибка сохранения доски:', error);
      }
    },
    startEditingBoardName() {
      this.isEditingBoardName = true;
      this.$nextTick(() => {
        this.$refs.boardNameInput.focus();
      });
    },
    async stopEditingBoardName() {
      this.isEditingBoardName = false;
      await this.saveBoard();
    },
    async addColumn() {
      const color = COLORS[this.board.columns.length % COLORS.length];
      const newColumn = {
        name: 'Новая колонка',
        color,
        board: this.board.id, 
      };

      try {
        const response = await axios.post('/api/columns/', newColumn, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.board.columns.push(response.data);
      } catch (error) {
        const errorMessage = error.response && error.response.data 
          ? error.response.data 
          : error.message;
        console.error('Ошибка загрузки досок:', errorMessage);
      }
    },
    async deleteColumn(columnIndex) {
      const column = this.board.columns[columnIndex];
      try {
        await axios.delete(`/api/columns/${column.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.board.columns.splice(columnIndex, 1);
      } catch (error) {
        const errorMessage = error.response && error.response.data 
          ? error.response.data 
          : error.message;
        console.error('Ошибка загрузки досок:', errorMessage);
      }
    },
    updateColumn(updatedColumn) {
      const index = this.board.columns.findIndex(col => col.id === updatedColumn.id);
      if (index !== -1) {
        this.board.columns[index] = updatedColumn;
      }
    },
    addTask(columnIndex) {
      this.currentTask = {
        name: '',
        description: '',
        subtasks: [],
        files: [],
        column: this.board.columns[columnIndex].id, 
      };
      this.currentColumnIndex = columnIndex;
      this.showModal = true;
    },
    async saveTask(savedTask) {
      try {
        // Находим колонку по ID
        const columnIndex = this.board.columns.findIndex(col => col.id === savedTask.column);
        
        if (columnIndex !== -1) {
          // Обновляем или добавляем задачу в UI
          const taskIndex = this.board.columns[columnIndex].tasks.findIndex(t => t.id === savedTask.id);
          
          if (taskIndex !== -1) {
            // Заменяем существующую задачу
            // this.$set(this.board.columns[columnIndex].tasks, taskIndex, savedTask);
            this.board.columns[columnIndex].tasks[taskIndex] = savedTask;
          } else {
            // Добавляем новую задачу
            this.board.columns[columnIndex].tasks.push(savedTask);
          }
        }
      } catch (error) {
        console.error('Ошибка обновления задачи на доске:', error);
      }
    },
    async deleteTask(task) {
      const columnIndex = this.board.columns.findIndex(col =>
        col.tasks.some(t => t.id === task.id)
      );
      if (columnIndex !== -1) {
        const taskIndex = this.board.columns[columnIndex].tasks.indexOf(task);
        this.board.columns[columnIndex].tasks.splice(taskIndex, 1);
        await this.saveBoard();
      }
    },
    async updateColumnTasks(columnIndex, tasks) {
      try {
        this.board.columns[columnIndex].tasks = tasks;
        
        await this.fetchBoardData();
        
        // Обновляем порядок задач на сервере
        for (let i = 0; i < tasks.length; i++) {
          const task = tasks[i];
          await axios.patch(`/api/tasks/${task.id}/`, 
            { 
              column: this.board.columns[columnIndex].id,
              order: i 
            }, 
            {
              headers: {
                Authorization: `Bearer ${localStorage.getItem('token')}`
              }
            }
          );
        }
      } catch (error) {
        console.error('Ошибка обновления порядка задач:', error);
      }
    },
    openModal(task) {
      this.currentTask = { ...task };
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.currentTask = {
        id: null,
        name: '',
        description: '',
        subtasks: [],
        files: [],
      };
      this.currentColumnIndex = null;
    },
    // Добавляем метод для открытия задачи из URL
    async openTaskFromQuery(taskId) {
      try {
        const response = await axios.get(`/api/tasks/${taskId}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.currentTask = response.data;
        this.showModal = true;
      } catch (error) {
        console.error('Ошибка загрузки задачи:', error);
      }
    },
    async generateBoardReport() {
      try {
        const response = await axios.get(`/api/reports/`, {
          params: {
            report_type: 'projects',
            board_id: this.id
          },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Создаем рабочую книгу Excel
        const ws = XLSX.utils.json_to_sheet(response.data.projects);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Board Report');
        
        // Добавляем лист с общей статистикой
        const summaryData = [
          ['Всего проектов', response.data.statistics.total_projects],
          ['Активных проектов', response.data.statistics.active_projects],
          ['Завершённых проектов', response.data.statistics.completed_projects]
        ];
        const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
        XLSX.utils.book_append_sheet(wb, summaryWs, 'Summary');
        
        // Генерируем имя файла с датой
        const date = new Date().toISOString().split('T')[0];
        const filename = `board_report_${this.id}_${date}.xlsx`;
        
        // Скачиваем файл
        XLSX.writeFile(wb, filename);
      } catch (error) {
        console.error('Ошибка при формировании отчёта:', error);
        if (error.response) {
          console.error('Response data:', error.response.data);
          console.error('Response status:', error.response.status);
        }
        alert('Произошла ошибка при формировании отчёта. Пожалуйста, попробуйте снова.');
      }
    },
  },
};
</script>

<style scoped>
.board {
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.board-header {
  margin-bottom: 16px;
}

.board-title-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
}

.board-title {
  max-width: 200px;
  font-size: 24px;
  font-weight: bold;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
}

.board-title:hover {
  background: #ecedf0;
}

.board-title-input {
  font-size: 24px;
  font-weight: bold;
  width: 100%;
  padding: 8px;
  border: 2px solid #0079bf;
  border-radius: 4px;
  outline: none;
}

.columns-container {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.columns {
  display: flex;
  gap: 16px;
}

.add-column-button {
  background: #f0f0f0;
  border: none;
  color: #5e6c84;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  min-width: 280px;
}

.add-column-button:hover {
  background: #e0e0e0;
}

.members-button {
  background: #f0f0f0;
  border: none;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.report-button {
  background-color: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
  margin-left: 10px;
}

.report-button:hover {
  background-color: #45a049;
}
</style>