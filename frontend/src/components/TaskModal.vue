<template>
  <div class="modal">
    <div class="modal-content">
      <input v-model="taskData.name" placeholder="Task Name">
      <textarea v-model="taskData.description" placeholder="Description"></textarea>
      
      <div class="subtasks">
        <div v-for="(subtask, index) in taskData.subtasks" :key="index" class="subtask">
          <input type="checkbox" v-model="subtask.is_completed">
          <input v-model="subtask.name">
          <button @click="deleteSubtask(index)">×</button>
        </div>
      </div>
      
      <button @click="addSubtask">Add Subtask</button>
      <button @click="saveTask">Save</button>
      <button @click="closeModal">Close</button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    task: Object
  },
  data() {
    return {
      taskData: {...this.task, subtasks: [...this.task.subtasks]}
    }
  },
  methods: {
    async saveTask() {
      await fetch(`/api/tasks/${this.taskData.id}/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.taskData)
      })
      this.$emit('update:task', this.taskData)
      this.closeModal()
    },
    addSubtask() {
      this.taskData.subtasks.push({
        name: '',
        is_completed: false,
        task: this.taskData.id
      })
    },
    async deleteSubtask(index) {
      const subtask = this.taskData.subtasks[index]
      if (subtask.id) {
        await fetch(`/api/subtasks/${subtask.id}/`, { method: 'DELETE' })
      }
      this.taskData.subtasks.splice(index, 1)
    },
    closeModal() {
      this.$emit('close')
    }
  }
}
</script>
