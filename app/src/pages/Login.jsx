import '@ant-design/v5-patch-for-react-19';
import React,{useState} from 'react';
import { Button, Checkbox, Form, Input,Typography,Space, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Login() {
      const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const [messageApi, contextHolder] = message.useMessage();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // 🔹 Send credentials to backend
      const response = await axios.post('http://127.0.0.1:8000/login', {
        username: values.username,
        password: values.password,
      });

      // const token = "dummy-jwt-token-123";
      
      // 🔹 Extract token (adjust key if your API returns differently)
      const { token } = response.data;

      // 🔹 Store token in localStorage
      localStorage.setItem('authToken', token);

      // 🔹 Show success message
      message.success('Login successful!',3);

      // 🔹 Redirect to dashboard
      navigate('/dashboard');

    } catch (error) {
      console.error(error);
      message.error('Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };
  const onFinishFailed = errorInfo => {
    console.log('Failed:', errorInfo);
  }
  const { Title } = Typography;
  return (
      

    <div className='login'>
      
      <Title level={2} style={{ textAlign: 'center', marginBottom: 20 }}>
        Login
      </Title>

      <Form
        className='login-form'
        name="basic"
        requiredMark={false}
        // labelCol={{ span: 24 }}
        // wrapperCol={{ span: 24 }}
        layout="vertical"
        style={{ maxWidth: 600 }}
        initialValues={{ remember: true }}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        autoComplete="off"
      >
        <Form.Item
          label="Username"
          name="username"
          rules={[{ required: true, message: 'Please input your username!' }]}
        >
          <Input />
        </Form.Item>

        <Form.Item
          label="Password"
          name="password"
          rules={[{ required: true, message: 'Please input your password!' }]}
        >
          <Input.Password />
        </Form.Item>

        <Form.Item name="remember" valuePropName="checked" label={null}>
          <Checkbox>Remember me</Checkbox>
        </Form.Item>

        <Form.Item label={null}>
          <Button type="primary" htmlType="submit">
            Submit
          </Button>
        </Form.Item>

        <Form.Item>
          <p>
            Don’t have an account? <a href="/register">Register</a>
          </p>
        </Form.Item>

      </Form>
    </div>
  );
}

export default Login;
