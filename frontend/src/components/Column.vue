<template>
  <div class="column">
    <div class="column-header">
      <input v-model="column.name" placeholder="Column Name" />
    </div>
    <div class="tasks">
      <Task
        v-for="(task, index) in column.tasks"
        :key="index"
        :task="task"
        @delete="deleteTask(index)"
        @click="openTaskModal(task)"
      />
    </div>
    <button @click="addTask">Add Task</button>
  </div>
</template>

<script>
import Task from './Task.vue';

export default {
  components: {
    Task,
  },
  props: {
    column: Object,
  },
  methods: {
    addTask() {
      const taskName = prompt('Enter task name');
      if (taskName) {
        this.$emit('addTask', taskName);
      }
    },
    deleteTask(taskIndex) {
      this.$emit('deleteTask', taskIndex);
    },
    openTaskModal(task) {
      this.$emit('openTaskModal', task);
    },
  },
};
</script>

<style scoped>
.column {
  border: 1px solid #ccc;
  padding: 10px;
  margin-right: 20px;
  border-radius: 5px;
}
.column-header {
  margin-bottom: 10px;
}
.tasks {
  margin-top: 10px;
}
</style>
