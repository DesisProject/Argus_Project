const API_BASE_URL = "/api";


export const loginUser = async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
    });

    if (!response.ok) {
        throw new Error("Invalid email or password");
    }

    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    return data;
};

export const registerUser = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }), 
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Registration failed. Email might already exist.");
    }

    return await response.json();
};

export const logoutUser = () => {
    localStorage.removeItem("token");
};

export const getToken = () => {
    return localStorage.getItem("token");
};
