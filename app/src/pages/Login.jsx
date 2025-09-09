import React from 'react';
import { Button, Checkbox, Form, Input,Typography } from 'antd';


function Login() {
    const onFinish = values => {
    console.log('Success:', values);
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
