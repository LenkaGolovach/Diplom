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
        <div class="header-buttons">
          <button @click="showMembersModal = true" class="members-button">
            👥 Участники
          </button>
          <button class="add-column-button" @click="addColumn">
            + Добавить колонку
          </button>
        </div>
      </div>
    </div>

    <div class="columns-container">
      <div class="columns">
        <Column
          v-for="(column, index) in board.columns"
          :key="column.id"
          :column="column"
          @add-task="(taskName) => addTask(index, taskName)"
          @update-column="updateColumn"
          @delete-column="() => deleteColumn(index)"
          @update-tasks="tasks => updateColumnTasks(index, tasks)"
          @openTaskModal="openModal"
        />
      </div>
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
      type: String,
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
  async created() {
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
        const response = await axios.get(`/api/boards/${this.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
          params: {
            include_tasks: true // Добавляем параметр для включения задач
          }
        });
        // Гарантируем наличие массива columns
        this.board = {
          ...response.data,
          columns: response.data.columns.map(column => ({
            ...column,
            tasks: column.tasks || [] // Гарантируем наличие массива задач
          }))
        };
        
        // Инициализируем задачи для каждой колонки
        this.board.columns.forEach(col => {
          col.tasks = col.tasks || [];
        });
      } catch (error) {
        console.error('Ошибка загрузки доски:', error);
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
    async updateColumn(column) {
      try {
        await axios.put(`/api/columns/${column.id}/`, column, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
      } catch (error) {
        const errorMessage = error.response && error.response.data 
          ? error.response.data 
          : error.message;
        console.error('Ошибка загрузки досок:', errorMessage);
      }
    },
    addTask(columnIndex, taskName = '') {
      this.currentTask = {
        name: taskName,
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
  },
};
</script>

<style scoped>
.board {
  height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, 
    #ffffff 0%,
    #fff5f5 25%,
    #f8f7ff 50%,
    #fff5f5 75%,
    #ffffff 100%
  );
}

.board-header {
  padding: 16px 30px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.07);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
}

.board-title-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-buttons {
  display: flex;
  gap: 15px;
  align-items: center;
}

.board-title {
  font-size: 22px;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: #2c3e50;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  letter-spacing: 0.3px;
  transition: all 0.3s ease;
}

.board-title:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateY(-1px);
}

.board-title-input {
  font-size: 22px;
  font-weight: 600;
  padding: 6px 12px;
  border: 2px solid #5a9bd4;
  border-radius: 8px;
  width: 300px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  box-shadow: 0 0 0 3px rgba(90, 155, 212, 0.2);
  outline: none;
}

.columns-container {
  flex: 1;
  overflow-x: auto;
  padding: 30px;
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}

.columns-container::-webkit-scrollbar {
  height: 8px;
}

.columns-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.columns-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.columns-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.columns {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  padding-bottom: 20px;
  min-height: calc(100vh - 150px);
  gap: 20px;
}

.members-button, .add-column-button {
  padding: 12px 18px;
  border: none;
  border-radius: 10px;
  font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
  font-weight: 500;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  letter-spacing: 0.3px;
}

.members-button {
  background: #f0f0f0;
  color: #4a5568;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.members-button:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.07);
}

.add-column-button {
  background: #5b9cff;
  color: white;
  box-shadow: 0 4px 15px rgba(91, 156, 255, 0.3);
}

.add-column-button:hover {
  background: #4a8bff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(91, 156, 255, 0.4);
}

@media (max-width: 768px) {
  .board-header {
    padding: 16px 20px;
  }
  
  .board-title-wrapper {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .header-buttons {
    width: 100%;
    justify-content: flex-end;
  }
  
  .board-title-input {
    width: 100%;
  }
  
  .columns-container {
    padding: 20px;
  }
}
</style>