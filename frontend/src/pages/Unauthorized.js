import React, { useState } from "react";


const Unauthorized = () => {
    const [selectedCategory, setSelectedCategory] = useState("");

    return (
        <div>
          <h1>Access Denied</h1>
          <p>You do not have permission to view this page.</p>
        </div>
      );
};

export default Unauthorized;





  