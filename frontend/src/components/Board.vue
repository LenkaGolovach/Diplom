<template>
  <div class="board">
    <div class="board-header">
      <input v-model="boardName" @change="updateBoardName" placeholder="Board Name" />
      <button @click="addColumn">Add Column</button>
    </div>
    <div class="columns">
      <Column
        v-for="(column, index) in columns"
        :key="index"
        :column="column"
        @addTask="addTask(index, $event)"
        @deleteTask="deleteTask"
      />
    </div>
    <TaskModal
      v-if="showModal"
      :task="currentTask"
      @close="closeModal"
    />
  </div>
</template>

<script>
import Column from './Column.vue';
import TaskModal from './TaskModal.vue';

export default {
  components: {
    Column,
    TaskModal,
  },
  data() {
    return {
      boardName: 'My Board',
      columns: [
        { name: 'To Do', tasks: [] },
        { name: 'In Progress', tasks: [] },
        { name: 'Done', tasks: [] },
      ],
      showModal: false,
      currentTask: null,
    };
  },
  methods: {
    updateBoardName() {
      // Logic to update board name
    },
    addColumn() {
      this.columns.push({ name: 'New Column', tasks: [] });
    },
    addTask(columnIndex, taskName) {
      this.columns[columnIndex].tasks.push({ name: taskName, description: '', subtasks: [] });
    },
    deleteTask(columnIndex, taskIndex) {
      this.columns[columnIndex].tasks.splice(taskIndex, 1);
    },
    openModal(task) {
      this.currentTask = task;
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
    },
  },
};
</script>

<style scoped>
.board {
  display: flex;
  flex-direction: column;
}
.board-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.columns {
  display: flex;
}
</style>
