<template>
	<view>
		<!-- 这是标准的html标签 -->
		<h1>我是about页面</h1>
		<!-- 这是view标签，为了跨平台开的标签，相当于div -->
		<!-- {{}}插值表达式，获取js中的变量 -->
		<!-- <view>用户名是:{{username}}</view> -->
		<button @click="onLogin">登录</button>
		<input type="text" v-model="mobile"  placeholder="请输入手机号"/>
		<view v-if="islogin==='notlogin'">请您登录</view>
		<view v-else-if="islogin==='login'">欢迎您：{{username}}</view>
		<table>
			<tbody>
				<!-- for data in 列表 -->
				<tr v-for="book in books" >
					<td>{{book.name}}</td>
					<td>{{book.author}}</td>
				</tr>
			</tbody>
		</table>
		
		<view>{{person.name}}</view>
		<view>{{person.age}}</view>
		<button @click="changName">改名</button>
	</view>
</template>

<script setup>
	// 导入vue的ref库  ref是专门创建响应式变量用的
	// 响应式，首先是我js的变量值变了，页面效果马上响应，跟着变
	import {ref,watch,reactive, onMounted} from "vue"
	
	// 比如我们要访问后台，可以放在这样的一个函数中，保证正常运行
	onMounted(()=>{
			 console.log("onMounted生命周期方法！");
	})
	// 定义响应式对象
	let person=reactive({
		"name":"zhangsan",
		"age":18
	})
	
	const changName=()=>{
		person.name="lisi"
	}
	
	let books = ref([{
	    "name": "三国演义",
	    "author": "罗贯中"
	  }, {
	    "name": "水浒传",
	    "author": "施耐庵"
	  }, {
	    "name": "红楼梦",
	    "author": "曹雪芹"
	  }, {
	    "name": "西游记",
	    "author": "吴承恩"
	  }])
	
	// ajax向后台查看是否登录 如果没有登录，变量 notlogin 登录 login
	let islogin=ref("login")
	
	
	let mobile = ref("")
	// watch(mobile,(value,oldValue)=>{
	// 	console.log("value:"+mobile.value)
	// })
	
	setTimeout(()=>{
		// 在vue中，改变变量的数值，需要用.value
		console.log("value:"+mobile.value)
	},2000)
	
	
	const onLogin=()=>{
		console.info("点击按钮了")
	}
	
	let username = ref("")
	// setTimeout函数，过多长时间，执行一个函数
	setTimeout(()=>{
		// 在vue中，改变变量的数值，需要用.value
		username.value="张三"
	},2000)
</script>

<style>
	       
</style>
