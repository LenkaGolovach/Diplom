<template>
  <div class="board">
    <div class="board-header">
      <div
        v-if="!isEditingBoardName"
        class="board-title"
        @dblclick="startEditingBoardName"
      >
        {{ board.name }}
      </div>
      <input
        v-else
        ref="boardNameInput"
        v-model="board.name"
        @blur="stopEditingBoardName"
        @keyup.enter="stopEditingBoardName"
        class="board-title-input"
      />
    </div>

    <div class="columns-container">
      <div class="columns">
        <Column
          v-for="(column, index) in board.columns"
          :key="column.id"
          :column="column"
          @add-task="addTask(index)"
          @delete-column="deleteColumn(index)"
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
  </div>
</template>

<script>
import Column from '../components/Column.vue';
import TaskModal from '../components/TaskModal.vue';
import axios from 'axios';

const COLORS = [
  '#61bd4f', '#f2d600', 
  '#ff9f1a', '#eb5a46', 
  '#c377e0', '#0079bf'
];

export default {
  components: {
    Column,
    TaskModal,
  },
  props: {
    id: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      board: {
        name: '',
        columns: [],
      },
      showModal: false,
      currentTask: {
        id: Date.now(),
        name: '',
        description: '',
        subtasks: [],
        files: [],
      },
      currentColumnIndex: null,
      isEditingBoardName: false,
    };
  },
  async created() {
    await this.fetchBoardData();
  },
  methods: {
    async fetchBoardData() {
      try {
        const response = await axios.get(`/api/boards/${this.id}/`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        this.board = response.data;
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
        id: Date.now(),
        name: 'Новая колонка',
        tasks: [],
        color,
      };
      this.board.columns.push(newColumn);
      await this.saveBoard();
    },
    async deleteColumn(columnIndex) {
      this.board.columns.splice(columnIndex, 1);
      await this.saveBoard();
    },
    addTask(columnIndex) {
      this.currentTask = {
        id: Date.now(),
        name: '',
        description: '',
        subtasks: [],
        files: [],
      };
      this.currentColumnIndex = columnIndex;
      this.showModal = true;
    },
    async saveTask(task) {
      if (this.currentColumnIndex !== null) {
        this.board.columns[this.currentColumnIndex].tasks.push(task);
      } else {
        const columnIndex = this.board.columns.findIndex(col =>
          col.tasks.some(t => t.id === this.currentTask.id)
        );
        if (columnIndex !== -1) {
          const taskIndex = this.board.columns[columnIndex].tasks.findIndex(
            t => t.id === this.currentTask.id
          );
          this.board.columns[columnIndex].tasks.splice(taskIndex, 1, task);
        }
      }
      this.closeModal();
      await this.saveBoard();
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
      this.board.columns[columnIndex].tasks = tasks;
      await this.saveBoard();
    },
    openModal(task) {
      this.currentTask = task;
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
      this.currentTask = null;
      this.currentColumnIndex = null;
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

.board-title {
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
</style>