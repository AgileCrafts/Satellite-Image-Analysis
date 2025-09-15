import React,{useState} from 'react';
import { Button, Checkbox, Form, Input, Typography, message } from 'antd';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

const Register = () => {
const [loading, setLoading] = useState(false);
const navigate = useNavigate(); 

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // Fake API call (replace with your backend API when ready)
      const response = await axios.post('http://127.0.0.1:8000/register', {
        username: values.username,
        email: values.email,
        password: values.password,
      });

      console.log(FormData)
      console.log("Response:", response.data);

      // Simulate success message
      message.success('Registration successful! You can now login.',3);

      // Redirect to dashboard
      navigate('/');

    } catch (error) {
      console.error(error);
      message.error('Registration failed. Try again later.');

      if (error.response?.data?.detail) {
      message.error(error.response.data.detail); // show backend validation error
    } else {
      message.error("Registration failed. Try again later.");
    }

    } finally {
      setLoading(false);
    }
  };
  const onFinishFailed = (errorInfo) => {
  console.log('Failed:', errorInfo);
  message.error('Please check the form and try again!');
  };

  return (
    <div className="register">
      <Title level={2} style={{ textAlign: 'center', marginBottom: 20 }}>
        Registration
      </Title>

      <Form
        className="register-form"
        name="register"
        requiredMark={false}
        layout="vertical"
        style={{ maxWidth: 600 }}
        initialValues={{ agreement: false }}
        onFinish={onFinish}
        onFinishFailed={onFinishFailed}
        autoComplete="off"
      >
        {/* Username */}
        <Form.Item
          label="Username"
          name="username"
          rules={[{ required: true, message: 'Please input your username!' }]}
        >
          <Input />
        </Form.Item>

        {/* Email */}
        <Form.Item
          label="Email"
          name="email"
          rules={[
            { required: true, message: 'Please input your email!' },
            { type: 'email', message: 'Please enter a valid email!' },
          ]}
        >
          <Input />
        </Form.Item>

        {/* Password */}
        <Form.Item
          label="Password"
          name="password"
          rules={[{ required: true, message: 'Please input your password!' }]}
        >
          <Input.Password />
        </Form.Item>

        {/* Confirm Password */}
        <Form.Item
          label="Confirm Password"
          name="confirmPassword"
          dependencies={['password']}
          rules={[
            { required: true, message: 'Please confirm your password!' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('Passwords do not match!'));
              },
            }),
          ]}
        >
          <Input.Password />
        </Form.Item>

        {/* Agreement Checkbox */}
        <Form.Item
          name="agreement"
          valuePropName="checked"
          rules={[
            {
              validator: (_, value) =>
                value
                  ? Promise.resolve()
                  : Promise.reject(new Error('You must accept the agreement')),
            },
          ]}
        >
          <Checkbox>I agree to the <a>terms and conditions</a></Checkbox>
        </Form.Item>

        {/* Submit */}
        <Form.Item>
          <Button type="primary" htmlType="submit" block>
            Register
          </Button>
        </Form.Item>

        <Form.Item>
          <p>
            Have an account? <a href="/">Login</a>
          </p>
        </Form.Item>
      </Form>
    </div>
  );
};

export default Register;
