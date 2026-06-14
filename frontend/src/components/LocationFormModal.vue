<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { createLocation, updateLocation } from '../api/location'
import type { Location, LocationFormData } from '../types/location'

const props = defineProps<{
  show: boolean
  location: Location | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)

const isEdit = computed(() => props.location !== null)

const defaultForm = (): LocationFormData => ({
  name: '',
  sort_order: 0,
})

const formModel = ref<LocationFormData>(defaultForm())

const rules: FormRules = {
  name: [{ required: true, message: '请输入地点名称', trigger: ['blur', 'input'] }],
  sort_order: [
    {
      type: 'number',
      required: true,
      message: '请输入排序序号',
      trigger: ['blur', 'input'],
    },
  ],
}

const modalTitle = computed(() => (isEdit.value ? '编辑地点' : '新增地点'))

watch(
  () => [props.show, props.location] as const,
  ([visible, location]) => {
    if (!visible) return
    if (location) {
      formModel.value = {
        name: location.name,
        sort_order: location.sort_order,
      }
    } else {
      formModel.value = defaultForm()
    }
  },
  { immediate: true },
)

function handleClose(): void {
  emit('update:show', false)
}

async function handleSubmit(): Promise<void> {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    if (isEdit.value && props.location) {
      await updateLocation(props.location.id, formModel.value)
      message.success('地点更新成功')
    } else {
      await createLocation(formModel.value)
      message.success('地点创建成功')
    }
    emit('saved')
  } catch (e: any) {
    const msg = e?.response?.data?.error || '提交失败，请稍后重试'
    message.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    :title="modalTitle"
    style="width: 460px"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="left"
      label-width="100"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="地点名称" path="name">
        <n-input v-model:value="formModel.name" placeholder="例如：楼道口" maxlength="32" />
      </n-form-item>

      <n-form-item label="排序序号" path="sort_order">
        <n-input-number
          v-model:value="formModel.sort_order"
          :min="0"
          :max="9999"
          placeholder="数值越小越靠前"
          style="width: 100%"
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="footer">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '创建' }}
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
