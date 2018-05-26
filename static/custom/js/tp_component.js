
Vue.component('doubt-list', {
  props: ['doubts', 'task_id', 'current_doubt', 'task_typ'],
  template: `
<table class="doubt-table">
<thead>
  <th>行数</th>
  <th>存疑文本</th>
  <th>存疑理由</th>
  <th>操作</th>
</thead>
<tbody>
  <tr v-for="(item, index) in doubts">
    <td>{{item.id}}</td>
    <td>{{item.doubt_text}}</td>
    <td>{{item.doubt_comment}}</td>
    <td><em  v-if="task_typ!=11" @click.native.prevent="deleteRow(index, doubts)">移除</em>
    <em v-else v-show="!scope.row.processed" @click.native.prevent="processRow(index, doubts)">完成处理</em></td>
  </tr>
</tbody>
`,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_doubt', val);
    },
    deleteRow(index, rows) {
      axios.delete('/api/doubt_seg/' + this.task_id + '/' + rows[index].id + '/delete/').then(function (response) {
        this.$delete(this.doubts, index)
        this.$emit('update:doubts', this.doubts);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });


    },
    processRow(index, rows) {
      rows[index].processed = true;
      axios.put('/api/doubt_seg/' + this.task_id + '/' + rows[index].id + '/', {
        task: this.task_id,
        processed: true
      }).then(function (response) {
        this.$emit('update:doubts', this.doubts);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    },
    loadDoubtSeg(){
      axios.get('/api/doubt_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
        this.$emit('update:doubts', _.reverse(response.data.models))
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    }
  },
  mounted() {
    this.loadDoubtSeg();
  }
})



Vue.component('mark-list', {
  props: ['marks', 'task_id', 'current_mark'],
  template: `
        <el-table
        :data="marks"
        :cell-style="{height: '20px'}"
        highlight-current-row
        @current-change="handleCurrentChange"
        style="width: 100%"
        max-height="200">
        <el-table-column
          prop="start"
          label="标记起点"
          >
        </el-table-column>
        <el-table-column
          prop="end"
          label="标记终点"
          >
        </el-table-column>
        <el-table-column
          prop="mark_typ"
          label="标记类型"
          >
          <template slot-scope="scope">
            <span >{{ typeStr(scope.row.mark_typ) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button 
              @click.native.prevent="deleteRow(scope.$index, marks)"
              type="text"
              size="small">
              移除
            </el-button>

          </template>
        </el-table-column>
      </el-table>
    `,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_mark', val);
    },
    typeStr(val) {
      switch (val) {
        case 1:  //标题
            return '标题';
        case 2: //作译者
            return '作译者';
        case 3: //序
            return '序';
        case 4: //正文
            return '正文';
        case 5: //跋
            return '跋';
        case 6: //偈颂
            return '偈颂';
        case 7: //夹注小字
            return '夹注小字';
        case 8: //梵文
            return '梵文';
        case 9: //咒语
            return '咒语';
        case 10: //行间小字
            return '行间小字';
      }
    },
    deleteRow(index, rows) {
      this.$delete(this.marks, index)
      this.$emit('update:marks', this.marks);
    },
    processRow(index, rows) {
      rows[index].processed = true;
      axios.put('/api/mark_seg/' + this.task_id + '/' + rows[index].id + '/', {
        task: this.task_id,
        processed: true
      }).then(function (response) {
        this.$emit('update:marks', this.marks);
      }.bind(this))
          .catch(function (error) {
            console.log(error)
          });
    },
    loadMarkSeg(){
      // axios.get('/api/mark_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
      //   this.$emit('update:marks', _.reverse(response.data.models))
      // }.bind(this))
      //     .catch(function (error) {
      //       console.log(error)
      //     });
    }
  },
  mounted() {
    this.loadMarkSeg();
  }
})


Vue.component('mark-doubt-list', {
  props: ['marks', 'task_id', 'current_mark', 'accept-this'],
  template: `
        <el-table
        :data="marks"
        :cell-style="{height: '20px'}"
        highlight-current-row
        @current-change="handleCurrentChange"
        style="width: 100%"
        max-height="200">
        <el-table-column
          prop="start"
          label="标记起点"
          >
        </el-table-column>
        <el-table-column
          prop="end"
          label="标记终点"
          >
        </el-table-column>
        <el-table-column
          prop="mark_typ"
          label="标记类型"
          width="100">
          <template slot-scope="scope">
            <span >{{ typeStr(scope.row.mark_typ) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          fixed="right"
          label="操作"
          width="120">
          <template slot-scope="scope">
            <el-button 
              @click.native.prevent="deleteRow(scope.$index, marks)"
              type="text"
              size="small">
              移除
            </el-button>
            <el-button 
              @click.native.prevent="processRow(scope.$index, marks)"
              type="text"
              size="small">
              接受
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    `,
  data() {
    return {}
  },
  methods: {
    handleCurrentChange(val) {
      this.$emit('update:current_mark', val);
    },
    typeStr(val) {
      switch (val) {
        case 1:  //标题
            return '标题';
        case 2: //作译者
            return '作译者';
        case 3: //序
            return '序';
        case 4: //正文
            return '正文';
        case 5: //跋
            return '跋';
        case 6: //偈颂
            return '偈颂';
        case 7: //夹注小字
            return '夹注小字';
        case 8: //梵文
            return '梵文';
        case 9: //咒语
            return '咒语';
        case 10: //行间小字
            return '行间小字';
      }
    },
    deleteRow(index, rows) {
      this.$delete(this.marks, index)
      this.$emit('update:marks', this.marks);
      this.$emit('update:current_mark', {});
    },
    processRow(index, rows) {
      rows[index].processed = true;
      this.$emit('accept', this.marks[index])
      this.deleteRow(index, rows)
    },
    loadMarkSeg(){
      // axios.get('/api/mark_seg/' + this.task_id + '/list/?task=' + this.task_id).then(function (response) {
      //   this.$emit('update:marks', _.reverse(response.data.models))
      // }.bind(this))
      //     .catch(function (error) {
      //       console.log(error)
      //     });
    }
  },
  mounted() {
    this.loadMarkSeg();
  }
})
