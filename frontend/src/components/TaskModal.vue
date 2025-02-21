<template>
  <div class="modal">
    <div class="modal-content">
      <!-- Заголовок формы -->
      <h2>Новая задача</h2>

      <!-- Поле для названия задачи -->
      <div class="form-group">
        <label for="task-name">Название задачи:</label>
        <input id="task-name" v-model="task.name" placeholder="Введите название задачи" />
      </div>

      <!-- Поле для описания задачи -->
      <div class="form-group">
        <label for="task-description">Описание задачи:</label>
        <textarea
          id="task-description"
          v-model="task.description"
          placeholder="Введите описание задачи"
        ></textarea>
      </div>

      <!-- Прогресс-бар -->
      <div class="progress-bar">
        <div class="progress" :style="{ width: progress + '%' }"></div>
      </div>
      <div class="progress-text">{{ progress }}% выполнено</div>

      <!-- Кнопка добавления подзадачи -->
      <button class="add-subtask-button" @click="addSubtask">Добавить подзадачу</button>

      <!-- Список подзадач -->
      <div class="subtasks">
        <div v-for="(subtask, index) in task.subtasks" :key="index" class="subtask">
          <input
            type="checkbox"
            v-model="subtask.completed"
            @change="updateProgress"
          />
          <input
            v-model="subtask.name"
            placeholder="Введите название подзадачи"
            :class="{ completed: subtask.completed }"
          />
          <!-- Кнопка удаления подзадачи (справа) -->
          <button @click="deleteSubtask(index)" class="delete-subtask-button">
            Удалить
          </button>
        </div>
      </div>

      <!-- Кнопки Save и Close -->
      <div class="actions">
        <button @click="saveTask" class="save-button">Сохранить</button>
        <button @click="closeModal" class="close-button">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    task: Object,
  },
  data() {
    return {
      progress: 0, // Прогресс выполнения подзадач
    };
  },
  watch: {
    // Следим за изменениями подзадач и обновляем прогресс
    'task.subtasks': {
      handler() {
        this.updateProgress();
      },
      deep: true,
    },
  },
  methods: {
    // Закрытие модального окна
    closeModal() {
      this.$emit('close');
    },

    // Сохранение задачи
    saveTask() {
      this.$emit('saveTask', this.task);
    },

    // Добавление подзадачи
    addSubtask() {
      this.task.subtasks.push({ name: '', completed: false });
    },

    // Удаление подзадачи
    deleteSubtask(index) {
      this.task.subtasks.splice(index, 1);
    },

    // Обновление прогресса выполнения подзадач
    updateProgress() {
      const totalSubtasks = this.task.subtasks.length;
      if (totalSubtasks === 0) {
        this.progress = 0;
        return;
      }
      const completedSubtasks = this.task.subtasks.filter(
        (subtask) => subtask.completed
      ).length;
      this.progress = Math.round((completedSubtasks / totalSubtasks) * 100);
    },
  },
  mounted() {
    // При открытии модального окна обновляем прогресс
    this.updateProgress();
  },
};
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 5px;
  width: 400px;
  max-width: 90%;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5em;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}

textarea {
  resize: vertical;
  min-height: 100px;
}

.progress-bar {
  width: 100%;
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  margin-bottom: 10px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #76c7c0;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  margin-bottom: 15px;
  font-size: 0.9em;
  color: #555;
}

.add-subtask-button {
  width: 100%;
  padding: 10px;
  background: #f0f0f0;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 15px;
}

.add-subtask-button:hover {
  background: #e0e0e0;
}

.subtasks {
  margin-bottom: 15px;
}

.subtask {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  gap: 10px; /* Расстояние между элементами */
}

.subtask input[type="checkbox"] {
  margin-right: 10px;
}

.subtask input[type="text"] {
  flex: 1; /* Занимает всё доступное пространство */
  padding: 5px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.subtask input[type="text"].completed {
  text-decoration: line-through;
  color: #888;
}

.delete-subtask-button {
  background: #ff6b6b;
  border: none;
  color: white;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: auto; /* Кнопка удаления сдвигается вправо */
}

.delete-subtask-button:hover {
  background: #ff4c4c;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.save-button,
.close-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.save-button {
  background: #76c7c0;
  color: white;
}

.save-button:hover {
  background: #5aa8a1;
}

.close-button {
  background: #f0f0f0;
  border: 1px solid #ccc;
}

.close-button:hover {
  background: #e0e0e0;
}
</style>