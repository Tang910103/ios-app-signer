//
//  NSTask-execute.swift
//  AppSigner
//
//  Created by Daniel Radtke on 11/3/15.
//  Copyright © 2015 Daniel Radtke. All rights reserved.
//

import Foundation
struct AppSignerTaskOutput {
    var output: String
    var status: Int32
    init(status: Int32, output: String){
        self.status = status
        self.output = output
    }
}
extension Process {
    func launchSynchronous() -> AppSignerTaskOutput {
        self.standardInput = FileHandle.nullDevice
        let pipe = Pipe()
        self.standardOutput = pipe
        self.standardError = pipe
        let pipeFile = pipe.fileHandleForReading
        self.launch()
        
        let data = NSMutableData()
        while self.isRunning {
            data.append(pipeFile.availableData)
        }
        
        pipeFile.closeFile();
        self.terminate();
        
        if let output = String.init(data: data as Data, encoding: String.Encoding.utf8) {
            return AppSignerTaskOutput(status: self.terminationStatus, output: output)
        } else {
            return AppSignerTaskOutput(status: self.terminationStatus, output: "")
        }
        
    }
    
    func execute(_ launchPath: String, workingDirectory: String?, arguments: [String]?)->AppSignerTaskOutput{
        self.launchPath = launchPath
        if arguments != nil {
            self.arguments = arguments
        }
        if workingDirectory != nil {
            self.currentDirectoryPath = workingDirectory!
        }
        return self.launchSynchronous()
    }

    func executeStreaming(
        _ launchPath: String,
        workingDirectory: String?,
        arguments: [String]?,
        onLine: @escaping (String) -> Void
    ) -> AppSignerTaskOutput {
        self.launchPath = launchPath
        if let arguments = arguments {
            self.arguments = arguments
        }
        if let workingDirectory = workingDirectory {
            self.currentDirectoryPath = workingDirectory
        }

        self.standardInput = FileHandle.nullDevice
        let pipe = Pipe()
        self.standardOutput = pipe
        self.standardError = pipe

        let data = NSMutableData()
        let lock = NSLock()
        var remainder = Data()
        let handle = pipe.fileHandleForReading

        handle.readabilityHandler = { fileHandle in
            let chunk = fileHandle.availableData
            if chunk.isEmpty { return }

            lock.lock()
            data.append(chunk)
            remainder.append(chunk)

            while let newlineIndex = remainder.firstIndex(of: 0x0A) {
                let lineData = remainder.subdata(in: 0..<newlineIndex)
                remainder.removeSubrange(0...newlineIndex)
                if let line = String(data: lineData, encoding: .utf8), !line.isEmpty {
                    onLine(line)
                }
            }
            lock.unlock()
        }

        self.launch()
        self.waitUntilExit()
        handle.readabilityHandler = nil

        lock.lock()
        if !remainder.isEmpty, let line = String(data: remainder, encoding: .utf8), !line.isEmpty {
            onLine(line)
        }
        let outputData = data as Data
        lock.unlock()

        handle.closeFile()
        self.terminate()

        if let output = String(data: outputData, encoding: .utf8) {
            return AppSignerTaskOutput(status: self.terminationStatus, output: output)
        } else {
            return AppSignerTaskOutput(status: self.terminationStatus, output: "")
        }
    }
    
}
