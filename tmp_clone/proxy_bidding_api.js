/**
 * API Proxy for Multi-Model Predictive Bidding System
 * 
 * This proxy forwards requests from the Node.js server to the Python Flask application
 * running on port 8080. It needs to be imported in server/routes.ts to be used.
 */

import express from 'express';
import axios from 'axios';

const { Router } = express;

// Python Flask API endpoint
const PYTHON_API_URL = 'http://localhost:8080';

// Create a router
const biddingRouter = Router();

// Proxy all bidding API requests to the Python Flask application
biddingRouter.all('/bidding/*', async (req, res) => {
  try {
    // Remove the /bidding prefix from the URL
    const path = req.path.replace('/bidding', '');
    
    // Forward the request to the Python Flask application
    const response = await axios({
      method: req.method,
      url: `${PYTHON_API_URL}${path}`,
      data: req.body,
      headers: {
        'Content-Type': 'application/json',
      },
      params: req.query,
    });
    
    // Send the response back to the client
    res.status(response.status).json(response.data);
  } catch (error) {
    console.error('Error forwarding request to Python API:', error);
    res.status(500).json({ error: 'Failed to forward request to Python API' });
  }
});

export default biddingRouter;