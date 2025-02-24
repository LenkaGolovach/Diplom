<template>
  <div class="board">
    <div class="board-header">
      <div
        v-if="!isEditingBoardName"
        class="board-title"
        @dblclick="startEditingBoardName"
      >
        {{ boardName }}
      </div>
      <input
        v-else
        ref="boardNameInput"
        v-model="boardName"
        @blur="stopEditingBoardName"
        @keyup.enter="stopEditingBoardName"
        class="board-title-input"
      />
    </div>

    <div class="columns-container">
      <div class="columns">
        <Column
          v-for="(column, index) in columns"
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
import Column from './Column.vue';
import TaskModal from './TaskModal.vue';

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
  data() {
    return {
      boardName: 'Моя доска',
      columns: [
        { id: 1, name: 'Нужно сделать', tasks: [], color: COLORS[0] },
        { id: 2, name: 'В процессе', tasks: [], color: COLORS[1] },
        { id: 3, name: 'Готово', tasks: [], color: COLORS[2] },
      ],
      showModal: false,
      currentTask: null,
      currentColumnIndex: null,
      isEditingBoardName: false,
    };
  },
  methods: {
    startEditingBoardName() {
      this.isEditingBoardName = true;
      this.$nextTick(() => {
        this.$refs.boardNameInput.focus();
      });
    },
    stopEditingBoardName() {
      this.isEditingBoardName = false;
    },
    addColumn() {
      const color = COLORS[this.columns.length % COLORS.length];
      const newColumn = {
        id: Date.now(), // Уникальный ID для новой колонки
        name: 'Новая колонка',
        tasks: [],
        color,
      };
      this.columns.push(newColumn);
    },
    addTask(columnIndex) {
      this.currentTask = {
        id: Date.now(),
        name: '',
        description: '',
        subtasks: [],
      };
      this.currentColumnIndex = columnIndex;
      this.showModal = true;
    },
    deleteTask(task) {
    const columnIndex = this.columns.findIndex(col => col.tasks.includes(task));
    if (columnIndex !== -1) {
      const taskIndex = this.columns[columnIndex].tasks.indexOf(task);
      this.columns[columnIndex].tasks.splice(taskIndex, 1);
    }
  },
    deleteColumn(columnIndex) {
      this.columns.splice(columnIndex, 1);
    },
    updateColumnTasks(columnIndex, tasks) {
      this.columns[columnIndex].tasks = tasks;
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
    saveTask(task) {
      if (this.currentColumnIndex !== null) {
        this.columns[this.currentColumnIndex].tasks.push(task);
      } else {
        const columnIndex = this.columns.findIndex(col => col.tasks.includes(this.currentTask));
        if (columnIndex !== -1) {
          const taskIndex = this.columns[columnIndex].tasks.indexOf(this.currentTask);
          this.columns[columnIndex].tasks.splice(taskIndex, 1, task);
        }
      }
      this.closeModal();
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