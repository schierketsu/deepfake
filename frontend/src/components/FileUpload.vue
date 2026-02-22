<template>
  <div class="content-block rounded-lg border-[3px] border-black p-6">
    <div
      @drop="handleDrop"
      @dragover.prevent
      @dragenter.prevent
      @dragleave="isDragging = false"
      @dragenter="isDragging = true"
      :class="[
        'rounded-lg border-[3px] border-black p-8 text-center transition-colors cursor-pointer',
        isDragging ? 'bg-gray-50' : 'bg-white hover:bg-gray-50'
      ]"
    >
        <input
          ref="fileInput"
          type="file"
          @change="handleFileSelect"
          accept="image/jpeg,image/jpg,image/png,image/heic,image/heif,video/mp4,video/quicktime,video/x-matroska,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          class="hidden"
        />

        <div class="flex flex-col items-center gap-4">
          <p class="title-sub">
            Перетащите файл сюда или нажмите для выбора
          </p>
          <div class="flex items-center justify-center gap-3 flex-wrap">
            <span class="title-sub text-base normal-case">изображение | видео | </span>
            <img :src="logopptxUrl" alt="PPTX" class="h-10 w-auto object-contain" />
            <img :src="logowordUrl" alt="Word" class="h-10 w-auto object-contain" />
          </div>
          <button
            @click="$refs.fileInput.click()"
            class="title-sub-white px-6 py-3 rounded-lg border-[3px] border-black bg-black hover:bg-gray-800 transition-colors"
          >
            ВЫБРАТЬ ФАЙЛ
          </button>
        </div>
      </div>

    <div v-if="error" class="mt-4 p-3 rounded-lg border-[3px] border-black bg-white">
      <p class="text-black text-xs">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { analyzeImage, analyzeVideo, analyzeDocument } from '../services/api'
import logopptxUrl from '../public/logopptx.png'
import logowordUrl from '../public/logoword.png'

export default {
  name: 'FileUpload',
  emits: ['file-uploaded', 'analysis-started', 'analysis-completed'],
  data() {
    return {
      logopptxUrl,
      logowordUrl,
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
      const isDocx = file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || (file.name && file.name.toLowerCase().endsWith('.docx'))
      
      if (!isImage && !isVideo && !isDocx) {
        this.error = 'Неподдерживаемый тип файла. Используйте изображения (JPEG, PNG, HEIC), видео (MP4, MOV, MKV) или Word (.docx)'
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
        } else if (file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || (file.name && file.name.toLowerCase().endsWith('.docx'))) {
          this.uploadProgress = 30
          result = await analyzeDocument(file)
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
        const detail = error.response?.data?.detail
        this.error = typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? (detail[0]?.msg || detail[0] || 'Произошла ошибка при анализе файла')
            : 'Произошла ошибка при анализе файла'
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
