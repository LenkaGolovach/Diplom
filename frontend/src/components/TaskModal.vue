<template>
  <div class="modal">
    <div class="modal-content">
      <!-- Заголовок задачи с возможностью редактирования -->
      <div class="task-header">
        <div
          v-if="!isEditingTitle"
          class="task-title"
          @dblclick="startEditingTitle"
        >
          {{ task.name || 'Новая задача' }}
        </div>
        <input
          v-else
          ref="titleInput"
          v-model="task.name"
          @blur="stopEditingTitle"
          @keyup.enter="stopEditingTitle"
          class="task-title-input"
          placeholder="Название задачи"
        />
      </div>

      <!-- Описание задачи -->
      <div class="form-group">
        <label>Описание:</label>
        <textarea
          v-model="task.description"
          placeholder="Введите описание задачи"
          class="description-input"
        ></textarea>
      </div>

      <!-- Прогресс-бар (только если есть подзадачи) -->
      <div v-if="hasSubtasks" class="progress-container">
        <div class="progress-bar">
          <div class="progress" :style="{ width: progress + '%' }"></div>
        </div>
        <div class="progress-text">{{ progress }}% выполнено</div>
      </div>

      <!-- Кнопка добавления подзадачи -->
      <button @click="addSubtask" class="add-subtask-button">
        + Добавить подзадачу
      </button>

      <!-- Список подзадач -->
      <div class="subtasks">
        <div v-for="(subtask, index) in task.subtasks" :key="index" class="subtask">
          <input
            type="checkbox"
            v-model="subtask.completed"
            @change="updateProgress"
          />
          <div
            class="subtask-title"
            @dblclick="startEditingSubtask(index)"
          >
            <template v-if="!subtask.editing">
              {{ subtask.name }}
            </template>
            <input
              v-else
              v-model="subtask.name"
              @blur="stopEditingSubtask(index)"
              @keyup.enter="stopEditingSubtask(index)"
              class="subtask-input"
            />
          </div>
          <button @click="deleteSubtask(index)" class="delete-subtask-button">
            ×
          </button>
        </div>
      </div>

      <!-- Секция для прикрепленных файлов -->
      <div class="file-section">
        <label>Прикрепленные файлы:</label>
        <div class="file-list">
          <div v-for="(file, index) in task.files" :key="index" class="file-item">
            <div class="file-preview" @click="downloadFile(file)">
              <img v-if="isImage(file.type)" :src="file.url" class="thumbnail">
              <div v-else class="file-icon">
                <img src="/icons/file-icon.png" alt="Document Icon" class="file-icon-img">
              </div>
            </div>
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <button @click="removeFile(index)" class="delete-file">×</button>
            </div>
          </div>
        </div>
        
        <label class="file-upload">
          <input 
            ref="fileInput"
            type="file" 
            @change="handleFileUpload" 
            multiple
            class="file-input"
          >
          <span class="upload-button">+ Добавить файлы</span>
        </label>
      </div>

      <!-- Кнопки управления -->
      <div class="actions">
        <button @click="saveTask" class="save-button">Сохранить</button>
        <button @click="closeModal" class="close-button">Закрыть</button>
      </div>
    </div>
  </div>
</template>

<script>
import { reactive } from 'vue';

export default {
  props: {
    task: Object,
  },
  data() {
    return {
      isEditingTitle: false,
      // Используем реактивную обертку для подзадач
      localTask: reactive({ ...this.task })
    };
  },
  computed: {
    progress() {
      if (!this.hasSubtasks) return 0;
      const completed = this.localTask.subtasks.filter(s => s.completed).length;
      return Math.round((completed / this.localTask.subtasks.length) * 100);
    },
    hasSubtasks() {
      return this.localTask.subtasks && this.localTask.subtasks.length > 0;
    }
  },
  methods: {
    startEditingTitle() {
      this.isEditingTitle = true;
      this.$nextTick(() => {
        this.$refs.titleInput.focus();
      });
    },
    stopEditingTitle() {
      this.isEditingTitle = false;
    },
    startEditingSubtask(index) {
      // Прямое изменение свойства с реактивным обновлением
      this.localTask.subtasks[index].editing = true;
      this.$nextTick(() => {
        const inputs = this.$el.querySelectorAll('.subtask-input');
        if (inputs[index]) inputs[index].focus();
      });
    },
    stopEditingSubtask(index) {
      this.localTask.subtasks[index].editing = false;
    },
    addSubtask() {
      if (!this.localTask.subtasks) {
        this.localTask.subtasks = [];
      }
      this.localTask.subtasks.push({
        name: 'Новая подзадача',
        completed: false,
        editing: false
      });
    },
    deleteSubtask(index) {
      this.task.subtasks.splice(index, 1);
    },
    updateProgress() {
      // Обновление прогресса происходит автоматически через computed свойство
    },
    closeModal() {
      this.$emit('close');
    },
    async saveTask() {
        const formData = new FormData()
        
        // Основные данные задачи
        formData.append('name', this.task.name)
        formData.append('description', this.task.description)
        formData.append('column', this.task.column.id)

        // Подзадачи
        this.task.subtasks.forEach((subtask, index) => {
            formData.append(`subtasks[${index}][name]`, subtask.name)
            formData.append(`subtasks[${index}][completed]`, subtask.completed)
        })

        // Файлы
        if (this.$refs.fileInput.files) {
            Array.from(this.$refs.fileInput.files).forEach(file => {
                formData.append('attachments', file)
            })
        }

        try {
            let response
            if (this.task.id) {
                // Обновление существующей задачи
                response = await axios.put(
                    `/api/tasks/${this.task.id}/`,
                    formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                            Authorization: `Bearer ${localStorage.getItem('token')}`
                        }
                    }
                )
            } else {
                // Создание новой задачи
                response = await axios.post(
                    '/api/tasks/',
                    formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data',
                            Authorization: `Bearer ${localStorage.getItem('token')}`
                        }
                    }
                )
            }
            
            this.$emit('saveTask', response.data)
            this.closeModal()
        } catch (error) {
            console.error('Ошибка сохранения задачи:', error)
            alert('Ошибка сохранения задачи')
        }
    },
    isImage(type) {
      return type.startsWith('image/');
    },
    handleFileUpload(e) {
      const files = Array.from(e.target.files); // Конвертируем FileList в массив
      
      // Проверяем наличие файлов
      if (!files || files.length === 0) return;

      // Сбрасываем значение инпута
      const resetInput = () => {
        this.$refs.fileInput.value = '';
      };

      files.forEach((file) => { // Используем forEach вместо for-loop
        const reader = new FileReader();
        
        reader.onload = (e) => {
          // Проверяем существование файла
          if (!file) return;

          // Инициализируем массив файлов если нужно
          if (!this.task.files) {
            this.$set(this.task, 'files', []);
          }

          // Добавляем файл в массив
          this.task.files.push({
            name: file.name,
            type: file.type,
            url: e.target.result
          });
        };

        reader.onerror = resetInput;
        reader.readAsDataURL(file);
      });

      resetInput();
    },
    removeFile(index) {
      if (this.task.files && this.task.files.length > index) {
        this.task.files.splice(index, 1);
      }
    },
    downloadFile(file) {
      // Создаем временную ссылку для скачивания
      const link = document.createElement('a');
      link.href = file.url;
      link.download = file.name; // Имя файла при скачивании
      document.body.appendChild(link);
      link.click(); // Инициируем скачивание
      document.body.removeChild(link); // Удаляем ссылку после скачивания
    },
  }
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
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
}

.task-header {
  margin-bottom: 20px;
}

.task-title {
  font-size: 1.5em;
  font-weight: bold;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
}

.task-title:hover {
  background: #f0f0f0;
}

.task-title-input {
  font-size: 1.5em;
  font-weight: bold;
  width: 100%;
  padding: 8px;
  border: 2px solid #0079bf;
  border-radius: 4px;
  margin-bottom: 15px;
  margin-right: 40px;
}

.description-input {
  width: 100%;
  min-height: 100px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 15px;
  margin-right: 40px;
}

.add-subtask-button {
  width: 100%;
  padding: 8px;
  background: #f0f0f0;
  border: none;
  border-radius: 4px;
  margin-bottom: 15px;
  cursor: pointer;
}

.subtasks {
  margin: 15px 0;
}

.subtask {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 8px;
}

.subtask-title {
  flex: 1;
  cursor: pointer;
  padding: 4px;
}

.subtask-input {
  flex: 1;
  padding: 4px;
  border: 1px solid #ddd;
}

.delete-subtask-button {
  background: #ff6b6b;
  border: none;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.progress-container {
  margin: 15px 0;
}

.progress-bar {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #76c7c0;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  font-size: 0.9em;
  color: #666;
  margin-top: 5px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.save-button {
  background: #76c7c0;
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.close-button {
  background: #f0f0f0;
  border: 1px solid #ccc;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.file-section {
  margin: 15px 0;
}

.file-list {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px;
  border: 1px solid #eee;
  border-radius: 4px;
  margin-bottom: 8px;
}

.file-preview {
  width: 40px;
  height: 40px;
  margin-right: 12px;
  cursor: pointer;
}

.thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
}

.file-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 4px;
}

.file-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-name {
  font-size: 0.9em;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-file {
  background: none;
  border: none;
  color: #ff6b6b;
  cursor: pointer;
  font-size: 1.2em;
  padding: 0 5px;
}

.file-upload {
  display: block;
  margin-top: 10px;
}

.file-input {
  display: none;
}

.upload-button {
  background: #f0f0f0;
  padding: 8px 15px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-block;
  transition: background 0.3s;
}

.upload-button:hover {
  background: #e0e0e0;
}

.file-icon-img {
  width: 24px; /* Размер иконки */
  height: 24px;
  object-fit: contain; /* Сохраняет пропорции */
}
</style>