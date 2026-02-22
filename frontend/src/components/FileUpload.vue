<template>
  <div class="content-block border-[3px] border-black p-6">
    <div
      @drop="handleDrop"
      @dragover.prevent
      @dragenter.prevent
      @dragleave="isDragging = false"
      @dragenter="isDragging = true"
      :class="[
        'border-[3px] border-black p-8 text-center transition-colors cursor-pointer',
        isDragging ? 'bg-gray-50' : 'bg-white hover:bg-gray-50'
      ]"
    >
        <input
          ref="fileInput"
          type="file"
          @change="handleFileSelect"
          accept="image/jpeg,image/jpg,image/png,image/heic,image/heif,video/mp4,video/quicktime,video/x-matroska"
          class="hidden"
        />

        <div class="space-y-4">
          <svg
            class="mx-auto h-8 w-8 text-black"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            stroke-width="1.5"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>

          <div class="space-y-1">
            <p class="text-sm font-medium text-black">
              Перетащите файл сюда или нажмите для выбора
            </p>
            <p class="text-xs text-gray-600">
              JPEG, PNG, HEIC | MP4, MOV, MKV
            </p>
          </div>

          <button
            @click="$refs.fileInput.click()"
            class="px-6 py-3 border-[3px] border-black bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            ВЫБРАТЬ ФАЙЛ
          </button>
        </div>
      </div>

    <div v-if="error" class="mt-4 p-3 border-[3px] border-black bg-white">
      <p class="text-black text-xs">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { analyzeImage, analyzeVideo } from '../services/api'

export default {
  name: 'FileUpload',
  emits: ['file-uploaded', 'analysis-started', 'analysis-completed'],
  data() {
    return {
      selectedFile: null,
      isDragging: false,
      error: null,
      uploadProgress: 0,
      MAX_FILE_SIZE: 100 * 1024 * 1024 // 100MB
    }
  },
  methods: {
    handleDrop(event) {
      event.preventDefault()
      this.isDragging = false
      
      const files = event.dataTransfer.files
      if (files.length > 0) {
        this.processFile(files[0])
      }
    },
    
    handleFileSelect(event) {
      const files = event.target.files
      if (files.length > 0) {
        this.processFile(files[0])
      }
    },
    
    processFile(file) {
      this.error = null
      this.uploadProgress = 0
      
      // Валидация размера
      if (file.size > this.MAX_FILE_SIZE) {
        this.error = `Файл слишком большой. Максимальный размер: ${this.formatFileSize(this.MAX_FILE_SIZE)}`
        return
      }
      
      // Валидация типа
      const isImage = file.type.startsWith('image/')
      const isVideo = file.type.startsWith('video/')
      
      if (!isImage && !isVideo) {
        this.error = 'Неподдерживаемый тип файла. Используйте изображения (JPEG, PNG, HEIC) или видео (MP4, MOV, MKV)'
        return
      }
      
      this.selectedFile = file
      this.analyzeFile(file)
    },
    
    async analyzeFile(file) {
      this.$emit('analysis-started')
      this.uploadProgress = 10
      
      try {
        let result
        
        if (file.type.startsWith('image/')) {
          this.uploadProgress = 30
          result = await analyzeImage(file)
        } else {
          this.uploadProgress = 30
          result = await analyzeVideo(file)
        }
        
        this.uploadProgress = 100
        // Передаем результат анализа вместе с информацией о файле
        this.$emit('file-uploaded', {
          ...result,
          fileInfo: {
            name: file.name,
            size: file.size
          }
        })
        this.$emit('analysis-completed')
        
      } catch (error) {
        console.error('Ошибка анализа:', error)
        this.error = error.response?.data?.detail || 'Произошла ошибка при анализе файла'
        this.$emit('analysis-completed')
      } finally {
        setTimeout(() => {
          this.uploadProgress = 0
        }, 1000)
      }
    },
    
    clearFile() {
      this.selectedFile = null
      this.error = null
      this.uploadProgress = 0
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
    }
  }
}
</script>
